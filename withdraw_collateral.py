from auto_core import AutoCore

if __name__ == "__main__":
    PHANTOM_PATH = "/absolute/path/to/phantom/extension"
    PROFILE_DIR = "/absolute/path/to/persistent/profile"

    core = AutoCore(
        phantom_path=PHANTOM_PATH,
        profile_dir=PROFILE_DIR,
        headless=False,
        slow_mo=100,
    )

    AMOUNT = 2.0  # Replace with test amount
    core.withdraw_collateral(amount=AMOUNT)
