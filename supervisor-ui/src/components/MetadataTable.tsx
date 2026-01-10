import { useMemo } from 'react';
import type { Sample, RDMPField, RawDataItem, StorageRoot } from '../types';

interface MetadataTableProps {
  samples: Sample[];
  fields: RDMPField[];
  rawData: RawDataItem[];
  loading: boolean;
  storageRoots?: StorageRoot[];
  onSelectSample?: (sample: Sample) => void;
}

export function MetadataTable({ samples, fields, rawData, loading, storageRoots = [], onSelectSample }: MetadataTableProps) {
  // Build a map of sample_id -> raw data info
  const rawDataBySample = useMemo(() => {
    const data: Record<number, { count: number; storageRootIds: Set<number> }> = {};
    for (const item of rawData) {
      if (item.sample_id) {
        if (!data[item.sample_id]) {
          data[item.sample_id] = { count: 0, storageRootIds: new Set() };
        }
        data[item.sample_id].count += 1;
        data[item.sample_id].storageRootIds.add(item.storage_root_id);
      }
    }
    return data;
  }, [rawData]);

  // Build storage root name lookup
  const storageRootNames = useMemo(() => {
    const names: Record<number, string> = {};
    for (const root of storageRoots) {
      names[root.id] = root.name;
    }
    return names;
  }, [storageRoots]);

  const getStorageRootNames = (storageRootIds: Set<number>) => {
    return Array.from(storageRootIds)
      .map(id => storageRootNames[id] || `Root ${id}`)
      .join(', ');
  };

  if (loading) {
    return <div style={styles.loading}>Loading samples...</div>;
  }

  if (samples.length === 0) {
    return (
      <div style={styles.empty}>
        <p>No samples in this project yet.</p>
      </div>
    );
  }

  if (fields.length === 0) {
    return (
      <div style={styles.empty}>
        <p>No RDMP fields defined for this project.</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Sample ID</th>
              {fields.map((field) => (
                <th key={field.key} style={styles.th}>
                  <div style={styles.headerContent}>
                    <span>{field.key}</span>
                    <span style={styles.fieldType}>
                      {field.type}
                      {field.required && <span style={styles.required}>*</span>}
                    </span>
                  </div>
                </th>
              ))}
              <th style={styles.th}>Files</th>
              <th style={styles.th}>Storage Roots</th>
              <th style={styles.th}>Status</th>
            </tr>
          </thead>
          <tbody>
            {samples.map((sample) => {
              const sampleData = rawDataBySample[sample.id];
              const fileCount = sampleData?.count || 0;
              const storageRootDisplay = sampleData
                ? getStorageRootNames(sampleData.storageRootIds)
                : '-';

              return (
                <tr
                  key={sample.id}
                  style={{
                    ...styles.row,
                    ...(onSelectSample ? styles.rowClickable : {}),
                  }}
                  onClick={() => onSelectSample?.(sample)}
                >
                  <td style={styles.td}>
                    <span style={styles.sampleId}>{sample.sample_identifier}</span>
                  </td>
                  {fields.map((field) => (
                    <td key={field.key} style={styles.td}>
                      {renderFieldValue(sample.fields[field.key], field)}
                    </td>
                  ))}
                  <td style={styles.td}>
                    <span style={styles.fileCount}>
                      {fileCount}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <span style={styles.storageRoots}>
                      {storageRootDisplay}
                    </span>
                  </td>
                  <td style={styles.td}>
                    {sample.completeness.is_complete ? (
                      <span style={styles.complete}>Complete</span>
                    ) : (
                      <span style={styles.incomplete}>
                        Missing: {sample.completeness.missing_fields.join(', ')}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={styles.legend}>
        <span style={styles.legendItem}>
          <span style={styles.required}>*</span> Required field
        </span>
        <span style={styles.legendItem}>
          {samples.length} sample{samples.length !== 1 ? 's' : ''}
        </span>
        <span style={styles.legendItem}>
          {fields.length} field{fields.length !== 1 ? 's' : ''}
        </span>
        <span style={styles.legendItem}>
          {rawData.length} file{rawData.length !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}

function renderFieldValue(value: unknown, field: RDMPField): React.ReactNode {
  if (value === undefined || value === null) {
    return <span style={styles.empty}>-</span>;
  }

  switch (field.type) {
    case 'number':
      return <span style={styles.number}>{String(value)}</span>;
    case 'date':
      return <span style={styles.date}>{String(value)}</span>;
    case 'categorical':
      return <span style={styles.categorical}>{String(value)}</span>;
    default:
      return <span>{String(value)}</span>;
  }
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '20px',
  },
  tableWrapper: {
    overflowX: 'auto',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    background: 'white',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '14px',
  },
  th: {
    padding: '12px 16px',
    textAlign: 'left',
    background: '#f9fafb',
    borderBottom: '2px solid #e5e7eb',
    fontWeight: 600,
    color: '#374151',
    whiteSpace: 'nowrap',
  },
  headerContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
  },
  fieldType: {
    fontSize: '11px',
    fontWeight: 400,
    color: '#9ca3af',
  },
  required: {
    color: '#dc2626',
    marginLeft: '2px',
  },
  row: {
    borderBottom: '1px solid #e5e7eb',
  },
  rowClickable: {
    cursor: 'pointer',
    transition: 'background 0.15s',
  },
  td: {
    padding: '12px 16px',
    verticalAlign: 'top',
  },
  sampleId: {
    fontWeight: 500,
    color: '#2563eb',
  },
  empty: {
    color: '#9ca3af',
    fontStyle: 'italic',
  },
  number: {
    fontFamily: 'monospace',
    color: '#059669',
  },
  date: {
    color: '#7c3aed',
  },
  categorical: {
    background: '#e0e7ff',
    color: '#3730a3',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '12px',
  },
  fileCount: {
    background: '#f3f4f6',
    color: '#4b5563',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 500,
  },
  storageRoots: {
    fontSize: '12px',
    color: '#6b7280',
    fontStyle: 'italic',
  },
  complete: {
    color: '#059669',
    fontWeight: 500,
  },
  incomplete: {
    color: '#dc2626',
    fontSize: '12px',
  },
  loading: {
    padding: '40px',
    textAlign: 'center',
    color: '#666',
  },
  legend: {
    marginTop: '12px',
    display: 'flex',
    gap: '20px',
    fontSize: '12px',
    color: '#6b7280',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
};
