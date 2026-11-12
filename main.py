from dify_plugin import DifyPluginEnv, Plugin

# Request Approval and Get Approval can wait up to 9 minutes for an answer.
plugin = Plugin(DifyPluginEnv(MAX_REQUEST_TIMEOUT=600))

if __name__ == "__main__":
    plugin.run()
