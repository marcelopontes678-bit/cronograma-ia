// Single source of truth for timing. Read by the 3D scene AND the audio synth,
// so every sound lands on the exact frame of its action.

export const FPS = 30;
export const DURATION = 20;

// Shot boundaries (cuts)
export const SHOT = {
  s1: 0.0,   // workshop, building the rocket
  s2: 3.4,   // lighting the fuse
  s3: 5.8,   // the rocket fails
  s4: 8.2,   // frustration -> idea
  s5: 10.9,  // booster + tape
  s6: 14.0,  // second attempt, launch
  s7: 16.0,  // exterior, fireworks
  s8: 17.6,  // ending, Clawd lit by fireworks
  end: 20.0,
};

export const EV = {
  fadeIn: [0.0, 0.7],
  wrenchHits: [0.95, 1.4, 1.85],
  hopLand: 2.92,

  match1: 3.75,          // match strike
  fuse1On: 4.3,          // fuse lit
  fuse1Out: 6.35,        // spark reaches the rocket
  match1Drop: 4.55,
  pfft: 6.62,
  toppleStart: 7.0,
  toppleHit: 7.55,
  toppleBounce: 7.78,

  sigh: 8.75,
  ideaLook: 10.0,
  idea: 10.15,           // "ding"
  dash: 10.62,

  liftUp: 11.45,         // rocket back upright (clank)
  pushStart: 11.75,
  pushHit: 12.05,        // booster touches rocket (clank)
  tape1: [12.15, 12.6],  // unroll window
  tape1Rip: 12.63,
  tape2: [12.75, 13.25],
  tape2Rip: 13.28,
  pats: [13.47, 13.7],

  match2: 14.15,
  fuse2On: 14.45,
  match2Drop: 14.6,
  ignite: 15.0,
  liftoff: 15.05,
  crash: 15.75,          // skylight glass breaks

  bursts: [16.65, 16.98, 17.3, 18.05, 18.62, 19.18],
  fadeOut: [19.3, 20.0],
};

// Launch kinematics shared by scene and audio (y in world units)
export const LAUNCH_ACC = 58;
