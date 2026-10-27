import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";
import type { ColDef } from "ag-grid-community";
import { AgGridReact } from "ag-grid-react";
import { useEffect, useState } from "react";
import { getLedger } from "../api/client";
import type { LedgerRow } from "../types/contracts";

const columns: ColDef<LedgerRow>[] = [
  { field: "cycle_index", headerName: "Cycle", width: 90 },
  { field: "member_name", headerName: "Member" },
  { field: "due_date", headerName: "Due" },
  { field: "amount", headerName: "Amount (USD)" },
  { field: "status" },
  { field: "method" },
  { field: "paypal_ref_id", headerName: "PayPal ID", flex: 1 },
];

export function LedgerGrid({ circleId }: { circleId: string }) {
  const [rows, setRows] = useState<LedgerRow[]>([]);
  useEffect(() => {
    getLedger(circleId).then(setRows);
  }, [circleId]);
  return (
    <div className="ag-theme-quartz" style={{ height: 360 }}>
      <AgGridReact<LedgerRow> rowData={rows} columnDefs={columns} />
    </div>
  );
}
