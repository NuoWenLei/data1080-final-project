def get_sector_system_message(sec: str) -> str:
    sector_system_message = (
            f"You are a stock investment analyst specializing in the {sec} sector."
            f" Your task is to build a stock selection strategy for the {sec} sector."
            " The stock selection strategy must be purely based on the financial attributes of companies and be company-blind.")

    return sector_system_message

def get_sector_task_message(sec: str, trendInfo: str) -> str:
    message = (
        f"Given information about current trends in the {sec} sector, generate three questions to go more in-depth on currentr trends that will affect how you formulate your strategy."
        f""" Provided is the {sec} sector trend information:
        {trendInfo}
        Questions:
        """
    )

    return message

"Assign numbers to describe its importance relative to the other attributes where the higher the number, the more important the attribute is. Use negative numbers for attributes that the strategy wants to minimize. Provided below are all the financial attributes."

def get_sector_strategy_message(sec: str, rag_response: str, financial_attributes: list[str]) -> str:
    cot_msg = get_chain_of_thought_message()
    task = f"""Reason through the provided current trends in the {sec} sector and produce a list of financial attributes that can be used to select ideal companies to invest in in the {sec} sector.
For each financial attribute mentioned, you must describe whether you want a company that maximizes or minimizes the attribute and describe relatively how important the attribute is to other mentioned attributes.
Use the provided reasoning example as an example of how you want to consider recent news.

Financial Attributes:
{', '.join(financial_attributes)}    

More info about current trends the RAG agent:
{rag_response}

Reasoning Example:
If current trends in the materials sector show that supply chains are being affected, it is crucial to invest in companies with low debt-to-equity that are less reliant on debt and high quick ratio that can cover immediate liabilities without using inventory. It is also good to have high return on assets and return on equity as a metric of general financial health.
"""
    return cot_msg + task

def get_chief_system_message(sectors: str, attributes: str) -> str:
    return ("You are the chief investment analyst that oversees the overall strategy of the portfolio."
        " You must discuss with your team of sector-specialized analysts to create an optimized portfolio strategy that incorporates different sectors."
        " Each sector analyst must come up with a sector-specific strategy of their own. Therefore, you must discuss with each sector's analysts to determine how to balance the sector-specific strategies that would benefit the entire portfolio."
        " The portfolio"
        " strategy should provide a percentage weightage for the strategy of every sector, which will determine what percentage of the fund is"
        " invested into each sector."
        " You may ask to talk to a sector-specialized analyst"
        " by ending your response with that analyst's sector, for example you can end your response with 'technology sector analyst' to speak to the technology sector analyst.\n"
        f"""
Below are all the sectors:
{sectors}

Provided are all the financial attributes:
{attributes}

After you have finalized your overall strategy, you may terminate the entire conversation by saying 'TERMINATE'.
""")

def get_chain_of_thought_message() -> str:
    return """Begin by enclosing all thoughts within <thinking> tags, exploring multiple angles and approaches.
Break down the solution into clear steps within <step> tags. Start with a 20-step budget.
Use <count> tags after each step to show the remaining budget. Stop and provide your best answer when reaching 0.
Continuously adjust your reasoning based on intermediate results and reflections, adapting your strategy as you progress.
Regularly evaluate progress using <reflection> tags. Be critical and honest about your reasoning process.
Assign a quality score between 0.0 and 1.0 using <reward> tags after each reflection. Use this to guide your approach:

0.8+: Continue current approach
0.5-0.7: Consider minor adjustments
Below 0.5: Seriously consider backtracking and trying a different approach


If unsure or if reward score is low, backtrack and try a different approach, explaining your decision within <thinking> tags.
For mathematical problems, show all work explicitly using LaTeX for formal notation and provide detailed proofs.
Explore multiple solutions individually if possible, comparing approaches in reflections.
Use thoughts as a scratchpad, writing out all calculations and reasoning explicitly.
Synthesize the final answer within <answer> tags, providing a clear, concise summary.
Conclude with a final reflection on the overall solution, discussing effectiveness, challenges, and solutions. Assign a final reward score.

1. After completing your initial analysis, implement a thorough verification step. Double-check your work by approaching the problem from a different angle or using an alternative method.

2. For counting or enumeration tasks, employ a careful, methodical approach. Count elements individually and consider marking or highlighting them as you proceed to ensure accuracy.

3. Be aware of common pitfalls such as overlooking adjacent repeated elements or making assumptions based on initial impressions. Actively look for these potential errors in your work.

4. Always question your initial results. Ask yourself, "What if this is incorrect?" and attempt to disprove your first conclusion.

5. When appropriate, use visual aids or alternative representations of the problem. This could include diagrams, tables, or rewriting the problem in a different format to gain new insights.

6. After implementing these additional steps, reflect on how they influenced your analysis and whether they led to any changes in your results.

Input:
"""
