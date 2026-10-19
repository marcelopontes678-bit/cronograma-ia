import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(95);
Config.setOverwriteOutput(true);
// Quadros com muito blur/mix-blend: em máquinas sem GPU a CPU satura; dê mais folga ao delayRender.
Config.setDelayRenderTimeoutInMilliseconds(240000);
Config.setConcurrency(3);
// Ambientes sem acesso à internet: aponte para um Chrome/Chromium local, p. ex.
//   REMOTION_BROWSER_EXECUTABLE=/caminho/chrome-headless-shell npm run render
if (process.env.REMOTION_BROWSER_EXECUTABLE) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER_EXECUTABLE);
}
