from autogen_agentchat.agents import AssistantAgent
from typing import Callable
from system_messages import get_sector_task_message

def create_individual_strategy(agent: AssistantAgent, query_rag: Callable[[str], str], sector: str):
	initial_trend_info = query_rag(f"Give a summary about current trends in the {sector} sector.")
	response = agent.run(task = get_sector_task_message())
	print(f"Agent response: {response}")
	rag_output = query_rag(response)
	agent.run(task = task_2(rag_output))
	pass