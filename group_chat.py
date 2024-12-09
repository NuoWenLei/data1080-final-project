import asyncio, os, json
from autogen_ext.models import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.task import TextMentionTermination
from dotenv import load_dotenv
from answer_extractor import extractor
from constants import SECTORS
from system_messages import get_sector_system_message, get_chief_system_message
from sector_chat import create_individual_strategy
from portfolio_gen import generate_final_stock_portfolio
# import tiktoken
# from graphrag.query.structured_search.global_search.search import GlobalSearch
# from graphrag.query.llm.oai.chat_openai import ChatOpenAI
# from graphrag.query.llm.oai.typing import OpenaiApiType

load_dotenv()

import subprocess

def query_rag(query: str) -> str:
  """Queries the GraphRAG for up-to-date information."""
  # Capture the output of a command
  result = subprocess.run(["graphrag", "query", "--root", ".", "--method", "global", "--query", f'"{query}"'], capture_output=True, text=True)
  return "\n\n".join(result.stdout.strip().split("\n\n")[1:])


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
All Financial Attributes:
{', '.join(get_financial_attributes())}

Strategy Discussion:
{strategy}
"""
"""
Sample Response:
{
  "audit risk": 5,
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
            new_result = dict()
            for k in result:
                new_result[k.lower()] = result[k]
            with open(f"weightages/sectors/{sector}_strategy.json", "w") as strategy_json:
                json.dump(new_result, strategy_json)
            return True
        except Exception as e:
            print(e)
            return False
        
    return determine_sector_strategy

def determine_overall_strategy(strategy: str) -> bool:
    """Processes the overall portfolio strategy into weightages of sectors, and then stores the dictionary into a JSON file."""
    import openai
    client = openai.Client(api_key=os.environ.get("GRAPHRAG_API_KEY"))
    response = client.chat.completions.create(model="gpt-4o-mini", messages = [
        {
            "role": "system",
            "content": "You are a JSON-formatting agent. Your task is to only return formatted JSON. Do not return anything else"
        },
        {
            "role": "user",
            "content": "Convert the following strategy into a JSON dictionary that maps from sector to a number. Provided below are all the sectors, the strategy to be converted, and a sample response."
            f"""
All Sectors:
{SECTORS}

Strategy:
{strategy}
"""
"""
Sample Response:
{
  "Technology": 0.5,
  "Consumer Defensive": 0.1,
  "Communication Services": 0.2
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
        with open(f"weightages/overall_strategy.json", "w") as strategy_json:
            json.dump(result, strategy_json)
        return True
    except Exception as e:
        print(e)
        return False

def get_financial_attributes():
    with open("tickers/weighable_attributes.json", "r") as weigh_json:
        attributes = json.load(weigh_json)
    return attributes

async def main() -> None:
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=os.environ.get("GRAPHRAG_API_KEY"))
    
    attributes = get_financial_attributes()

    sector_agent_names = {
        "main": "ChiefAnalyst",
        "chief": "ChiefAnalyst"
    }
    for sec in SECTORS:
        sector_agent_names[sec.lower()] = f"{sec.replace(' ', '')}SectorAnalyst"

    sector_agents = []
    sector_strategies = []
    for sec in SECTORS:
      print(f"{sec} SECTOR")
      agent = AssistantAgent(
          f"{sec.replace(' ', '')}SectorAnalyst",
          model_client,
          description=f"A stock investment analyst specializing in the {sec} sector",
          system_message=get_sector_system_message(sec = sec))
      strategy = await create_individual_strategy(agent, query_rag, sec, attributes)
      sector_agents.append(agent)
      sector_strategies.append(extractor(strategy))
    
    print("SECTOR STRATEGIES")
    print(sector_strategies)
    main_agent = AssistantAgent(
        "ChiefAnalyst",
        model_client,
        description="The chief investment analyst that oversees all sector-specific stock analysts",
        system_message=get_chief_system_message(sectors = SECTORS, attributes = attributes, strategies=sector_strategies)
    )

    def selector_func(messages):
        cleaned = messages[-1].content.strip().lower()
        valid_characters = " abcdefghijklmnopqrstuvwxyz"
        response = ""
        for c in cleaned:
            if c in valid_characters:
              response += c
        sector_text = response.split(" ")[-10:]
        for sector_key in sector_agent_names:
            if sector_key in sector_text:
                return sector_agent_names[sector_key]
            
        if sector_text[-1] == "terminate":
            return None
        return "ChiefAnalyst"

    termination = TextMentionTermination("TERMINATE")
    team = SelectorGroupChat(
        sector_agents + [main_agent],
        model_client=model_client,
        selector_func=selector_func,
        termination_condition=termination,
    )

    stream = team.run_stream(task="Generate a robust multi-sector stock investment strategy based on global trends and the current U.S. market. main")
    last_message = ""
    async for message in stream:
        print(message)
        last_message = message
    
    determine_overall_strategy(last_message)

    generate_final_stock_portfolio()


if __name__ == "__main__":
  asyncio.run(main())