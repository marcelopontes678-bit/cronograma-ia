import { C } from "../config";

/**
 * Silhueta masculina caminhando, vista de costas. Desenhada em unidades de altura (1 = corpo inteiro),
 * origem nos pés. `phase` é o ciclo do passo (0–1), controlado pelo frame de quem usa.
 */
export const WalkingMan: React.FC<{
  x: number;
  y: number; // chão (pés)
  height: number; // px
  phase: number;
  coat?: boolean;
  fill?: string;
  rim?: string;
  rimOpacity?: number;
  mirror?: boolean; // reflexo (espelhado no chão)
}> = ({ x, y, height, phase, coat = true, fill = "#05070a", rim = C.goldBright, rimOpacity = 0.16, mirror = false }) => {
  const TAU = Math.PI * 2;
  const s = Math.sin(TAU * phase);
  const c = Math.cos(TAU * phase);
  const bob = -Math.abs(c) * 0.007;
  const sway = s * 0.008;
  const lift = (p: number) => Math.max(0, Math.sin(TAU * (phase + p))) * 0.05;
  const liftL = lift(0);
  const liftR = lift(0.5);
  const hemSway = s * 0.012;
  const armL = s * 0.035;
  const armR = -s * 0.035;
  const strokeProps = { stroke: rim, strokeOpacity: rimOpacity, strokeWidth: 1.4, vectorEffect: "non-scaling-stroke" as const };

  const leg = (cx: number, lf: number) => (
    <g>
      <path
        d={`M ${cx - 0.046},-0.40 L ${cx + 0.046},-0.40 L ${cx + 0.036},${-0.025 - lf} L ${cx - 0.036},${-0.025 - lf} Z`}
        fill={fill}
        {...strokeProps}
      />
      <ellipse cx={cx} cy={-0.014 - lf} rx={0.050} ry={0.022} fill={fill} {...strokeProps} />
    </g>
  );

  return (
    <g transform={`translate(${x} ${y}) scale(${height} ${mirror ? -height : height})`}>
      <g transform={`translate(${sway} ${bob})`}>
        {leg(-0.050, liftL)}
        {leg(0.050, liftR)}
        {/* braços */}
        <path d={`M -0.128,-0.835 L -0.098,-0.835 L ${-0.128 - 0.012},${-0.50 + armL} L ${-0.172},${-0.50 + armL} Z`} fill={fill} {...strokeProps} />
        <path d={`M 0.128,-0.835 L 0.098,-0.835 L ${0.128 + 0.012},${-0.50 + armR} L ${0.172},${-0.50 + armR} Z`} fill={fill} {...strokeProps} />
        {/* tronco / casaco */}
        <path
          d={
            coat
              ? `M -0.130,-0.822 C -0.112,-0.858 -0.06,-0.872 0,-0.872 C 0.06,-0.872 0.112,-0.858 0.130,-0.822
                 C 0.140,-0.70 0.146,-0.58 0.150,-0.50 C 0.160,-0.42 0.172,-0.36 ${0.182 + hemSway},-0.300
                 L ${-0.182 + hemSway},-0.300 C -0.172,-0.36 -0.160,-0.42 -0.150,-0.50 C -0.146,-0.58 -0.140,-0.70 -0.130,-0.822 Z`
              : `M -0.130,-0.822 C -0.112,-0.858 -0.06,-0.872 0,-0.872 C 0.06,-0.872 0.112,-0.858 0.130,-0.822
                 C 0.128,-0.74 0.112,-0.64 0.108,-0.56 C 0.112,-0.50 0.124,-0.46 ${0.130 + hemSway * 0.6},-0.415
                 L ${-0.130 + hemSway * 0.6},-0.415 C -0.124,-0.46 -0.112,-0.50 -0.108,-0.56 C -0.112,-0.64 -0.128,-0.74 -0.130,-0.822 Z`
          }
          fill={fill}
          {...strokeProps}
        />
        {/* pescoço e cabeça */}
        <rect x={-0.022} y={-0.885} width={0.044} height={0.03} fill={fill} />
        <ellipse cx={0} cy={-0.928} rx={0.05} ry={0.062} fill={fill} {...strokeProps} />
        {/* gola */}
        {coat && <path d="M -0.05,-0.862 Q 0,-0.84 0.05,-0.862" fill="none" stroke={rim} strokeOpacity={0.18} strokeWidth={1.4} vectorEffect="non-scaling-stroke" />}
      </g>
    </g>
  );
};
