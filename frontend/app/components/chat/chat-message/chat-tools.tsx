import { ToolData } from "@/app/components/chat";
import { Artifact, CodeArtifact } from "@/app/components/chat/widgets/Artifact";
import { WeatherCard, WeatherData } from "@/app/components/chat/widgets/WeatherCard";

// TODO: If needed, add displaying more tool outputs here
export default function ChatTools({
  data,
  artifactVersion,
}: {
  data: ToolData;
  artifactVersion?: number;
}) {
  if (!data) return null;
  const { toolCall, toolOutput } = data;

  if (toolOutput.isError) {
    return (
      <div className="border-l-2 border-red-400 pl-2">
        There was an error when calling the tool {toolCall.name} with input:{" "}
        <br />
        {JSON.stringify(toolCall.input)}
      </div>
    );
  }

  switch (toolCall.name) {
    case "get_weather_information":
      const weatherData = toolOutput.output as unknown as WeatherData;
      return <WeatherCard data={weatherData} />;
    case "artifact":
      return (
        <Artifact
          artifact={toolOutput.output as CodeArtifact}
          version={artifactVersion}
        />
      );
    default:
      return null;
  }
}
