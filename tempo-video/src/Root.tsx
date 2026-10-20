import { Composition } from "remotion";
import { DURATION, FPS, HEIGHT, WIDTH } from "./config";
import { MainVideo } from "./MainVideo";
import { fontsReady, jpReady } from "./fonts";
import { FACELESS_DURATION, FacelessVideo } from "./faceless/FacelessVideo";
import { TOKYO_DURATION, TokyoNight } from "./tokyo/TokyoNight";
import { TOKYO_OPUS_DURATION, TokyoNightOpus } from "./tokyo/TokyoNightOpus";

void fontsReady;
void jpReady;

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
  <Composition id="TokyoNight" component={TokyoNight} durationInFrames={TOKYO_DURATION} fps={FPS} width={WIDTH} height={HEIGHT} />
  <Composition id="TokyoNightOpus" component={TokyoNightOpus} durationInFrames={TOKYO_OPUS_DURATION} fps={FPS} width={WIDTH} height={HEIGHT} />
  <Composition id="FacelessPT" component={FacelessVideo} durationInFrames={FACELESS_DURATION} fps={FPS} width={WIDTH} height={HEIGHT} />
  </>
);
