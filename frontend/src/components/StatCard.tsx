type Props = {
  title: string;
  value: string | number;
};

export default function StatCard({ title, value }: Props) {
  return (
    <div className="dashboard-card">
      <h4>{title}</h4>

      <h2>{value}</h2>
    </div>
  );
}
