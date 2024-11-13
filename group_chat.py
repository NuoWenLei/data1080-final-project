import asyncio, os, json
from autogen_ext.models import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.task import TextMentionTermination
from dotenv import load_dotenv

load_dotenv()

def get_sectors() -> list[str]:
  with open("tickers/sectors.json", "r") as sectors_json:
      sectors = json.dump(sectors_json)
  return sectors

async def main() -> None:
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini", api_key=os.environ.get("GRAPHRAG_API_KEY"))

    def check_caculation(x: int, y: int, answer: int) -> str:
        if x + y == answer:
            return "Correct!"
        else:
            return "Incorrect!"
        
    sectors = get_sectors()

    sector_agents = []
    for sec in sectors:
        sector_agents.append(AssistantAgent(
            f"{sec} Sector Analyst",
            model_client,
            tools=[query_rag], # TODO
            description=f"A stock investment analyst specializing in the {sec} sector",
            system_message=f"You are a stock investment analyst specializing in the {sec} sector. Use the tools at your disposal to analyze trends in the sector and communicate with other analysts to determine a stock selection strategy for your specialized sector that would benefit the overall portfolio as a whole. For example, if another sector has high risk investments, you may develop a strategy that balances out the high risks from other sectors.",
        ))
    
    mainAgent = AssistantAgent(
        "Chief Analyst",
        model_client,
        description="The chief investment analyst that oversees all sector-specific stock analysts",
        system_message="You are the chief investment analyst that "
    )

    agent1 = AssistantAgent(
        "Agent1",
        model_client,
        description="For calculation",
        system_message="Calculate the sum of two numbers",
    )
    agent2 = AssistantAgent(
        "Agent2",
        model_client,
        tools=[check_caculation],
        description="For checking calculation",
        system_message="Check the answer and respond with 'Correct!' or 'Incorrect!'",
    )

    def selector_func(messages):
        if len(messages) == 1 or messages[-1].content == "Incorrect!":
            return "Agent1"
        if messages[-1].source == "Agent1":
            return "Agent2"
        return None

    termination = TextMentionTermination("Correct!")
    team = SelectorGroupChat(
        [agent1, agent2],
        model_client=model_client,
        selector_func=selector_func,
        termination_condition=termination,
    )

    stream = team.run_stream("What is 1 + 1?")
    async for message in stream:
        print(message)


asyncio.run(main())