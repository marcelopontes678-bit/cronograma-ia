import { Composition } from "remotion";
import { DURATION, FPS, HEIGHT, WIDTH } from "./config";
import { MainVideo } from "./MainVideo";
import { fontsReady } from "./fonts";

void fontsReady;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="TempoVideo"
    component={MainVideo}
    durationInFrames={DURATION}
    fps={FPS}
    width={WIDTH}
    height={HEIGHT}
    defaultProps={{ showSafeArea: false }}
  />
);
