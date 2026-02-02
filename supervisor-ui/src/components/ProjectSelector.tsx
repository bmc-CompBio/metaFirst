import type { Project } from '../types';

interface ProjectSelectorProps {
  projects: Project[];
  selectedProjectId: number | null;
  onSelect: (projectId: number) => void;
  loading: boolean;
  onCreateProject?: () => void;
}

export function ProjectSelector({
  projects,
  selectedProjectId,
  onSelect,
  loading,
  onCreateProject,
}: ProjectSelectorProps) {
  if (loading) {
    return <div style={styles.loading}>Loading projects...</div>;
  }

  return (
    <div style={styles.container}>
      <label style={styles.label}>Select Project:</label>
      <select
        value={selectedProjectId ?? ''}
        onChange={(e) => onSelect(Number(e.target.value))}
        style={styles.select}
        disabled={projects.length === 0}
      >
        {projects.length === 0 ? (
          <option value="">No projects available</option>
        ) : (
          <>
            <option value="" disabled>
              Choose a project...
            </option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </>
        )}
      </select>
      {onCreateProject && (
        <button style={styles.createButton} onClick={onCreateProject}>
          + Create Project
        </button>
      )}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  label: {
    fontWeight: 500,
    color: '#374151',
  },
  select: {
    padding: '8px 12px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    background: 'white',
    minWidth: '250px',
    cursor: 'pointer',
  },
  loading: {
    color: '#666',
    fontStyle: 'italic',
  },
  createButton: {
    padding: '8px 16px',
    fontSize: '14px',
    fontWeight: 500,
    background: '#2563eb',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
};
