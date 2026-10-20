import { Composition } from "remotion";
import { DURATION, FPS, HEIGHT, WIDTH } from "./config";
import { MainVideo } from "./MainVideo";
import { fontsReady } from "./fonts";
import { FACELESS_DURATION, FacelessVideo } from "./faceless/FacelessVideo";

void fontsReady;

export const RemotionRoot: React.FC = () => (
  <>
  <Composition
    id="TempoVideo"
    component={MainVideo}
    durationInFrames={DURATION}
    fps={FPS}
    width={WIDTH}
    height={HEIGHT}
    defaultProps={{ showSafeArea: false }}
  />
  <Composition id="FacelessPT" component={FacelessVideo} durationInFrames={FACELESS_DURATION} fps={FPS} width={WIDTH} height={HEIGHT} />
  </>
);
