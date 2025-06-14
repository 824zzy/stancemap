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


if __name__ == "__main__":
    # Example usage
    prompt = (
        "Generate a report on the current state of renewable energy adoption worldwide."
    )
    report = generate_report(prompt)
    print(report)
