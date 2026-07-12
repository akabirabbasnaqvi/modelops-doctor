import {
  BarChart,
  Bar,
  XAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type Props = {
  driftedFeatures: string[];
};

export default function DriftChart({
  driftedFeatures,
}: Props) {
  const data =
    driftedFeatures.map(
      (feature) => ({
        feature,
        drift: 1,
      })
    );

  return (
    <ResponsiveContainer
      width="100%"
      height={300}
    >
      <BarChart data={data}>
        <XAxis dataKey="feature" />

        <Tooltip />

        <Bar
          dataKey="drift"
          fill="#ef4444"
        />
      </BarChart>
    </ResponsiveContainer>
  );
}