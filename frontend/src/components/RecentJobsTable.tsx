/**
 * The subset of an automation job this table renders. Declared structurally
 * rather than importing AutomationJob so the dashboard's lighter job summary
 * can be passed in too.
 */
type RecentJob = {
  id: number;
  job_type: string;
  status: string;
};

type Props = {
  jobs: RecentJob[];
};

export default function RecentJobsTable({
  jobs,
}: Props) {
  return (
    <table className="data-table">
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