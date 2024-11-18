def find_text_between(txt: str, start_str: str, end_str: str) -> str:
    """Finds and returns the text between start_str and end_str in the given txt."""
    # Find the starting and ending positions
    start_index = txt.find(start_str)
    end_index = txt.find(end_str, start_index)

    # Raise an error if either start_str or end_str is not found
    if start_index == -1 or end_index == -1:
        raise ValueError(f"Either '{start_str}' or '{end_str}' not found in the text.")

    # Extract and return the text between start_str and end_str
    return txt[start_index + len(start_str):end_index].strip()

# Example usage
text = "This is a Start sample code block End in the text."
result = find_text_between(text, "Start", "End")
print(result)  # Output: "sample code block"