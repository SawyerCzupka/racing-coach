from racing_coach_core.models.telemetry import TelemetrySequence


class ServerCommunicationManager:
    def __init__(self, server_url: str):
        self.server_url = server_url

    def send_telemetry_data(self, telemetry_data: TelemetrySequence):
        """
        Send telemetry data to the server.
        """
        # Here you would implement the logic to send the telemetry data to the server.
        # This could be done using requests or any other HTTP client library.
        # For example:
        # response = requests.post(f"{self.server_url}/telemetry", json=telemetry_data.to_dict())
        # return response.status_code == 200
        pass
