type Props = {
  title: string;
  value: string | number;
};

export default function StatCard({
  title,
  value,
}: Props) {
  return (
    <div
      style={{
        background: "white",
        borderRadius: "12px",
        padding: "20px",
        boxShadow:
          "0 1px 3px rgba(0,0,0,0.15)",
      }}
    >
      <h4>{title}</h4>

      <h2>{value}</h2>
    </div>
  );
}