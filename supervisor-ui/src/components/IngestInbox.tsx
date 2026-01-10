import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { PendingIngest, Project, StorageRoot } from '../types';

interface IngestInboxProps {
  project: Project;
  onSelectIngest: (ingest: PendingIngest) => void;
  storageRoots: StorageRoot[];
}

export function IngestInbox({ project, onSelectIngest, storageRoots }: IngestInboxProps) {
  const [pendingIngests, setPendingIngests] = useState<PendingIngest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPendingIngests = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.getPendingIngests(project.id, 'PENDING');
      setPendingIngests(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load pending ingests');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPendingIngests();
    // Refresh every 10 seconds
    const interval = setInterval(loadPendingIngests, 10000);
    return () => clearInterval(interval);
  }, [project.id]);

  const getStorageRootName = (storageRootId: number) => {
    const root = storageRoots.find(r => r.id === storageRootId);
    return root?.name || `Storage Root ${storageRootId}`;
  };

  const formatFileSize = (bytes: number | null) => {
    if (bytes === null) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading && pendingIngests.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h2 style={styles.title}>Ingest Inbox</h2>
        </div>
        <div style={styles.loading}>Loading pending ingests...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h2 style={styles.title}>Ingest Inbox</h2>
          <button onClick={loadPendingIngests} style={styles.refreshButton}>
            Refresh
          </button>
        </div>
        <div style={styles.error}>{error}</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>
          Ingest Inbox
          {pendingIngests.length > 0 && (
            <span style={styles.badge}>{pendingIngests.length}</span>
          )}
        </h2>
        <button onClick={loadPendingIngests} style={styles.refreshButton}>
          Refresh
        </button>
      </div>

      {pendingIngests.length === 0 ? (
        <div style={styles.empty}>
          <p>No pending files to ingest.</p>
          <p style={styles.emptyHint}>
            New files detected by the ingest helper will appear here.
          </p>
        </div>
      ) : (
        <div style={styles.list}>
          {pendingIngests.map((ingest) => (
            <div
              key={ingest.id}
              style={styles.card}
              onClick={() => onSelectIngest(ingest)}
            >
              <div style={styles.cardMain}>
                <div style={styles.filePath}>{ingest.relative_path}</div>
                <div style={styles.cardMeta}>
                  <span style={styles.storageRoot}>
                    {getStorageRootName(ingest.storage_root_id)}
                  </span>
                  <span style={styles.separator}>|</span>
                  <span>{formatFileSize(ingest.file_size_bytes)}</span>
                  <span style={styles.separator}>|</span>
                  <span>{formatDate(ingest.created_at)}</span>
                </div>
                {ingest.inferred_sample_identifier && (
                  <div style={styles.inferred}>
                    Suggested: {ingest.inferred_sample_identifier}
                  </div>
                )}
              </div>
              <div style={styles.cardAction}>
                <span style={styles.arrow}>&#8250;</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: '#fff',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    padding: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  title: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#111827',
    margin: 0,
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  badge: {
    background: '#f59e0b',
    color: '#fff',
    fontSize: '12px',
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: '12px',
  },
  refreshButton: {
    padding: '6px 12px',
    fontSize: '14px',
    background: '#f3f4f6',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    cursor: 'pointer',
    color: '#374151',
  },
  loading: {
    padding: '40px',
    textAlign: 'center',
    color: '#6b7280',
  },
  error: {
    padding: '16px',
    background: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '6px',
    color: '#dc2626',
  },
  empty: {
    padding: '40px',
    textAlign: 'center',
    color: '#6b7280',
  },
  emptyHint: {
    fontSize: '14px',
    marginTop: '8px',
    color: '#9ca3af',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  card: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    background: '#f9fafb',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  cardMain: {
    flex: 1,
    minWidth: 0,
  },
  filePath: {
    fontSize: '14px',
    fontWeight: 500,
    color: '#111827',
    fontFamily: 'monospace',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  cardMeta: {
    fontSize: '12px',
    color: '#6b7280',
    marginTop: '4px',
  },
  storageRoot: {
    color: '#2563eb',
    fontWeight: 500,
  },
  separator: {
    margin: '0 6px',
    color: '#d1d5db',
  },
  inferred: {
    fontSize: '12px',
    color: '#059669',
    marginTop: '4px',
    fontStyle: 'italic',
  },
  cardAction: {
    marginLeft: '16px',
  },
  arrow: {
    fontSize: '24px',
    color: '#9ca3af',
  },
};
