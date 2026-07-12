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

      <div
        style={{
          width: "180px",
          height: "180px",
          borderRadius: "50%",
          border: `12px solid ${color}`,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          fontSize: "32px",
          fontWeight: "bold",
        }}
      >
        {score}
      </div>
    </div>
  );
}