type Props = {
  score: number;
};

export default function HealthGauge({
  score,
}: Props) {
  let color = "#ef4444";

  if (score >= 80) {
    color = "#22c55e";
  } else if (score >= 60) {
    color = "#f59e0b";
  }

  return (
    <div>
      <h3>Health Score</h3>

      <div className="health-gauge" style={{ borderColor: color }}>
        {score}
      </div>
    </div>
  );
}