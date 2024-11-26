from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models import OpenAIChatCompletionClient
from typing import Callable
from system_messages import get_sector_task_message, get_sector_strategy_message, get_sector_system_message
import subprocess, os, json, asyncio

from dotenv import load_dotenv

load_dotenv()

def query_rag(query: str) -> str:
  """Queries the GraphRAG for up-to-date information."""
  # Capture the output of a command
  result = subprocess.run(["graphrag", "query", "--root", ".", "--method", "global", "--query", f'"{query}"'], capture_output=True, text=True)
  return "\n\n".join(result.stdout.strip().split("\n\n")[1:])

def get_financial_attributes():
    with open("tickers/weighable_attributes.json", "r") as weigh_json:
        attributes = json.load(weigh_json)
    return attributes

def determine_investment_strategy(sector: str):
    def determine_sector_strategy(strategy: str) -> bool:
        """Processes the sector strategy into weightages of attributes, and then stores the dictionary into a JSON file."""
        import openai
        client = openai.Client(api_key=os.environ.get("GRAPHRAG_API_KEY"))
        response = client.chat.completions.create(model="gpt-4o-mini", messages = [
            {
                "role": "system",
                "content": "You are a JSON-formatting agent. Your task is to only return formatted JSON. Do not return anything else"
            },
            {
                "role": "user",
                "content": "Convert the following strategy into a JSON dictionary that maps from financial attribute to a number describing its importance relative to the other attributes where the higher the number, the more important the attribute is. Use negative numbers for attributes that the strategy wants to minimize. Provided below are all the financial attributes, the strategy to be converted, and a sample response."
                f"""
    All Attributes:
    {get_financial_attributes()}

    Strategy:
    {strategy}
    """
    """
    Sample Response:
    {
      "audit risk": 5,
      "average volume 10days": 1,
      "total debt": -8,
      "earnings growth": 10,
      "total cash per share": 3
    }

    Respond in JSON format and do not include anything else.
    """
            }
        ])

        json_response = response.choices[0].message.content

        id1 = json_response.find("{")
        id2 = json_response.find("}")
        json_dict = json_response[id1:id2 + 1]
        try:
            result = json.loads(json_dict)
            with open(f"weightages/sectors/{sector}_strategy.json", "w") as strategy_json:
                json.dump(result, strategy_json)
            return True
        except Exception as e:
            print(e)
            return False
        
    return determine_sector_strategy

async def create_individual_strategy(agent: AssistantAgent, query_rag: Callable[[str], str], sector: str, financial_attributes: list[str]) -> str:
  initial_trend_info = query_rag(f"Give a summary about current trends in the {sector} sector.")
  task1 = get_sector_task_message(sector, initial_trend_info)
  print(f"Task 1: {task1}")
  print()
  response = await agent.run(task = task1)
  response = response.messages[-1].content
  print(f"Task 1 response: {response}")
  rag_output = query_rag(response)
  task2 = get_sector_strategy_message(sector, rag_output, financial_attributes)
  print(f"Task 2: {task2}")
  task2_output = await agent.run(task = task2)
  print(f"Task 2 Response: {task2_output.messages[-1].content}")
  determine_investment_strategy(sector)(task2_output.messages[-1].content)
  return task2_output.messages[-1].content

if __name__ == "__main__":
  sec = "Technology"
  model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=os.environ.get("GRAPHRAG_API_KEY"))
  sector_agent = AssistantAgent(
        f"TechnologySectorAnalyst",
        model_client,
        description=f"A stock investment analyst specializing in the {sec} sector",
        system_message=get_sector_system_message(sec = sec)
    )
  
  asyncio.run(create_individual_strategy(sector_agent, query_rag, sec, get_financial_attributes()))