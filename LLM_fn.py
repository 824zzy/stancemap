from credentials import OPENAI_API_KEY
import openai


def generate_report(prompt):
    """
    Generates a report based on the provided prompt using OpenAI's latest API.

    Args:
        prompt (str): The input prompt for the report generation.

    Returns:
        str: The generated report text.
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


def stance_analysis(claim, tweet):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a stance analysis assistant."},
            {
                "role": "user",
                "content": f"""
                    Analyze the truthfulness stance (whether the tweet believes the claim is true) of the following tweet toward the factual claim. Positive stance means the tweet believes the claim is true, Negative stance means the tweet believes the claim is false, and Neutral means the tweet does not express a clear opinion on the claim.
                    The output should be one of the following: "Positive", "Neutral", "Negative".
                    Only output one of these three words, with no explanation or extra text.
                    Claim: {claim}
                    Tweet: {tweet}
                """,
            },
        ],
    )
    result = response.choices[0].message.content.strip()
    if result not in {"Positive", "Neutral", "Negative"}:
        return "Neutral"
    return result


if __name__ == "__main__":
    # Example usage
    # prompt = (
    #     "Generate a report on the current state of renewable energy adoption worldwide."
    # )
    # report = generate_report(prompt)
    # print(report)

    claim = "The Earth is flat."
    tweet = (
        "I believe the Earth is flat because I don't see any curvature from my window."
    )
    stance = stance_analysis(claim, tweet)
    print(f"Stance on the claim '{claim}': {stance}")
