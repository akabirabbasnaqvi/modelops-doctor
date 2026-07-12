type Props = {
  jobs: any[];
};

export default function RecentJobsTable({
  jobs,
}: Props) {
  return (
    <table
      style={{
        width: "100%",
        borderCollapse: "collapse",
      }}
    >
      <thead>
        <tr>
          <th>ID</th>
          <th>Type</th>
          <th>Status</th>
        </tr>
      </thead>

      <tbody>
        {jobs.map((job) => (
          <tr key={job.id}>
            <td>{job.id}</td>

            <td>{job.job_type}</td>

            <td>{job.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}