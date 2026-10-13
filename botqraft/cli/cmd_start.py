from botqraft.runtime_args import RuntimeArgs


def run_botqraft(args: RuntimeArgs) -> None:
    """Run the standalone QQ runtime with the selected deployment arguments.
    
    :param args: Deployment action and selected configuration and permission paths.
    :return: No return value.
    """
    from botqraft.runtime import Runtime
    Runtime(args).run()
