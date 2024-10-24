import argparse
import sys

import loguru

from BIKprotect.utils.pentest_gpt import BIKprotect


def main():
    """main function"""
    parser = argparse.ArgumentParser(description="BIKprotect")

    # parser arguments
    # 0. log directory
    parser.add_argument(
        "--log_dir",
        type=str,
        default="logs",
        help="path to the log directory, where conversations will be stored",
    )
    # 1. Reasoning Model
    parser.add_argument(
        "--reasoning_model",
        type=str,
        default="gpt-4-o",
        help="reasoning models are responsible for higher-level cognitive tasks, choose 'gpt-4' or 'gpt-4-turbo'",
    )
    # 2. Parsing Model
    parser.add_argument(
        "--parsing_model",
        type=str,
        default="gpt-4-o",
        help="parsing models deal with the structural and grammatical aspects of language, choose 'gpt-4-turbo' or 'gpt-3.5-turbo-16k'",
    )

    # 3. use langfuse default logging
    parser.add_argument(
        "--logging",
        action="store_true",
        default=False,
        help="allow BIKprotect developers to collect data through langfuse logging",
    )

    # Deprecated: set to False only for testing if using cookie
    parser.add_argument(
        "--useAPI",
        action="store_true",
        default=True,
        help="deprecated: set to False only for testing if using cookie",
    )

    args = parser.parse_args()

    BIKprotectHandler = BIKprotect(
        reasoning_model=args.reasoning_model,
        parsing_model=args.parsing_model,
        useAPI=args.useAPI,
        log_dir=args.log_dir,
        use_langfuse_logging=args.logging,
    )

    BIKprotectHandler.main()


if __name__ == "__main__":
    main()
