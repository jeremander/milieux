
def yes_no_prompt(prompt: str) -> bool:
    """Issues a yes/no prompt to the user.
    Returns True if the user answers yes."""
    result = input(f'{prompt} [y/n] ')
    return result.lower().startswith('y')
