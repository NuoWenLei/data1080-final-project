import asyncio, os, json
from autogen_ext.models import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.task import TextMentionTermination
from dotenv import load_dotenv
from constants import SECTORS
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
  return result
# api_key = os.environ["GRAPHRAG_API_KEY"]
# llm_model = "gpt-4o-mini"

# llm = ChatOpenAI(
#     api_key=api_key,
#     model=llm_model,
#     api_type=OpenaiApiType.OpenAI,  # OpenaiApiType.OpenAI or OpenaiApiType.AzureOpenAI
#     max_retries=10,
# )

# token_encoder = tiktoken.encoding_for_model(llm_model)

# context_builder_params = {
#     "use_community_summary": False,  # False means using full community reports. True means using community short summaries.
#     "shuffle_data": True,
#     "include_community_rank": True,
#     "min_community_rank": 0,
#     "community_rank_name": "rank",
#     "include_community_weight": True,
#     "community_weight_name": "occurrence weight",
#     "normalize_community_weight": True,
#     "max_tokens": 12_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
#     "context_name": "Reports",
# }

# map_llm_params = {
#     "max_tokens": 1000,
#     "temperature": 0.0,
#     "response_format": {"type": "json_object"},
# }

# reduce_llm_params = {
#     "max_tokens": 2000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000-1500)
#     "temperature": 0.0,
# }

# context_builder = GlobalCommunityContext(
#     community_reports=reports,
#     communities=communities,
#     entities=entities,  # default to None if you don't want to use community weights for ranking
#     token_encoder=token_encoder,
# )

# search_engine = GlobalSearch(
#     llm=llm,
#     context_builder=context_builder,
#     token_encoder=token_encoder,
#     max_data_tokens=12_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
#     map_llm_params=map_llm_params,
#     reduce_llm_params=reduce_llm_params,
#     allow_general_knowledge=False,  # set this to True will add instruction to encourage the LLM to incorporate general knowledge in the response, which may increase hallucinations, but could be useful in some use cases.
#     json_mode=True,  # set this to False if your LLM model does not support JSON mode.
#     context_builder_params=context_builder_params,
#     concurrent_coroutines=32,
#     response_type="multiple paragraphs",  # free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
# )

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
        sector_agent_names[sec.lower()] = f"{sec.replace(" ", "")}SectorAnalyst"

    sector_agents = []
    for sec in SECTORS:
        sector_agents.append(AssistantAgent(
            f"{sec.replace(" ", "")}SectorAnalyst",
            model_client,
            tools=[query_rag, determine_investment_strategy(sec)], # TODO
            description=f"A stock investment analyst specializing in the {sec} sector",
            system_message=f"You are a stock investment analyst specializing in the {sec} sector."
            " You work with sector-specialized analysts in every sector as well as a chief investment analyst"
            " that oversees the entire portfolio strategy. Use the tools at your disposal to analyze trends"
            " in the sector and communicate with other analysts to determine a stock selection strategy for"
            " your specialized sector that would benefit the overall portfolio. The stock selection strategy"
            " must be purely based on the provided financial attributes of companies and be company-blind. For example, if another"
            " sector has high risk investments, you may develop a strategy that balances out the risks from other"
            " sectors by investing in low risk stocks. When you have finalized your stock selection strategy, call"
            " the determine_sector_strategy tool with a description of your strategy for picking stocks in this sector."
            " You may ask to talk to another sector-specialized analyst by ending your response with that analyst's sector, for example you can end your response with 'technology sector analyst' to speak to the technology sector analyst."
            " You may ask to talk to the chief investment analyst by ending your response with the word 'main', for example 'main analyst' or 'chief analyst'.\n"
            f"""Below are all the sectors:
{SECTORS}

Provided are all the financial attributes:
{attributes}
"""
        ))
    
    main_agent = AssistantAgent(
        "ChiefAnalyst",
        model_client,
        tools=[query_rag, determine_overall_strategy],
        description="The chief investment analyst that oversees all sector-specific stock analysts",
        system_message="You are the chief investment analyst that oversees the overall strategy of the portfolio."
        " You must discuss with your team of sector-specialized analysts to create an optimized portfolio strategy that incorporates different sectors."
        " Each sector analyst must come up with a sector-specific strategy of their own. Therefore, you must discuss with each sector's analysts to determine the sector-specific strategies that would benefit the entire portfolio."
        " There are tools to help give you up-to-date information about global news. The portfolio"
        " strategy should provide a percentage weightage for the strategy of every sector, which will determine what percentage of the fund is"
        " invested into each sector. When you have finalized your sector weightages, call the determine_overall_strategy"
        " tool with the numeric percentage weightages for every sector that you plan to invest in. You may ask to talk to a sector-specialized analyst"
        " by ending your response with that analyst's sector, for example you can end your response with 'technology sector analyst' to speak to the technology sector analyst.\n"
        f"""
Below are all the sectors:
{SECTORS}

Provided are all the financial attributes:
{attributes}

After you have finalized your overall strategy and every sector has finalized each of their strategies, you may terminate the entire conversation by saying 'TERMINATE'.
"""
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
    async for message in stream:
        print(message)


asyncio.run(main())