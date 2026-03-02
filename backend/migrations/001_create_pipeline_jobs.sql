CREATE TABLE IF NOT EXISTS pipeline_jobs (
  id_job INT NOT NULL AUTO_INCREMENT,
  id_partida INT NOT NULL,
  tipo VARCHAR(32) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
  payload_json JSON NULL,
  log_path TEXT NULL,
  error_message TEXT NULL,
  attempts INT NOT NULL DEFAULT 0,
  max_attempts INT NOT NULL DEFAULT 3,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id_job),
  KEY idx_pipeline_jobs_status (status),
  KEY idx_pipeline_jobs_tipo (tipo),
  KEY idx_pipeline_jobs_partida (id_partida),
  CONSTRAINT fk_pipeline_jobs_partida
    FOREIGN KEY (id_partida) REFERENCES partidas(id_partida)
    ON DELETE CASCADE
    ON UPDATE CASCADE
);