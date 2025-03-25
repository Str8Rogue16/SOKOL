import { useEffect, useState } from "react";

export default function Dashboard() {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:5000/get_reports")
      .then((res) => res.json())
      .then((data) => setReports(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Intelligence Reports</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reports.map((report, index) => (
          <div key={index} className="p-4 border rounded shadow">
            <h2 className="font-semibold">{report.title}</h2>
            <p className="text-sm">{report.source}</p>
            <a href={report.link} target="_blank" rel="noopener noreferrer" className="text-blue-500">
              Read More
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
