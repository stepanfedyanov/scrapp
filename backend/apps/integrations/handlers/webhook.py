from apps.integrations.registry import BaseIntegrationHandler


class WebhookHandler(BaseIntegrationHandler):
    def publish(self, integration, publish_target, content: dict):
        # basic stub - real implementation would perform HTTP POST
        # here we simply return the payload for logging
        return {'sent': content}
