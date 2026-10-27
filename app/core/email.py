def send_reset_email(to_email: str, reset_url: str) -> None:
    # Local stand-in. The reset link is printed in the API console.
    print("Password reset link")
    print(f"To: {to_email}")
    print(reset_url)

    # Deploy: send reset_url to to_email from here.
    # Keep this function name and these two arguments.
    # The forgot-password route stays as it is.

def send_invite_email(to_email: str, invite_url: str) -> None:
    print("Workspace invitation", flush=True)
    print(f"To: {to_email}", flush=True)
    print(invite_url, flush=True)