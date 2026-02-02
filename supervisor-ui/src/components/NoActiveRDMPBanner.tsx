import { useNavigate } from 'react-router-dom';

interface NoActiveRDMPBannerProps {
  projectId: number;
}

export function NoActiveRDMPBanner({ projectId }: NoActiveRDMPBannerProps) {
  const navigate = useNavigate();

  return (
    <div style={styles.banner}>
      <div style={styles.content}>
        <span style={styles.icon}>&#9888;</span>
        <div style={styles.text}>
          <span style={styles.title}>No Active RDMP</span>
          <span style={styles.description}>
            This project is not operational. Activate an RDMP to enable data ingestion.
          </span>
        </div>
      </div>
      <button
        style={styles.button}
        onClick={() => navigate(`/rdmps?project=${projectId}`)}
      >
        Go to RDMPs
      </button>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  banner: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    background: '#fffbeb',
    border: '1px solid #fde68a',
    borderRadius: '8px',
    marginBottom: '16px',
  },
  content: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  icon: {
    fontSize: '20px',
    color: '#f59e0b',
  },
  text: {
    display: 'flex',
    flexDirection: 'column',
  },
  title: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#92400e',
  },
  description: {
    fontSize: '13px',
    color: '#78350f',
  },
  button: {
    padding: '8px 16px',
    fontSize: '13px',
    fontWeight: 500,
    background: '#f59e0b',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
};
