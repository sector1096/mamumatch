-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Servidor: mariadb:3306
-- Tiempo de generación: 02-03-2026 a las 19:27:26
-- Versión del servidor: 11.4.5-MariaDB-log
-- Versión de PHP: 8.2.27

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `mamutero`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `alineaciones_evento_segmento`
--

CREATE TABLE `alineaciones_evento_segmento` (
  `id_alineacion` bigint(20) NOT NULL,
  `match_id` int(11) NOT NULL,
  `id_evento` bigint(20) DEFAULT NULL,
  `segment_id` int(11) DEFAULT NULL,
  `event_t` decimal(8,3) DEFAULT NULL,
  `seg_t` decimal(8,3) DEFAULT NULL,
  `delta_s` decimal(6,3) DEFAULT NULL,
  `matched` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Alinea eventos detectados en la partida con segmentos de audio/transcripción (whisper). Guarda tiempos, delta y flag de match.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `canales`
--

CREATE TABLE `canales` (
  `id_canal` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de canales (fuente o canal de contenido) usados para clasificar videos/casters.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `casters`
--

CREATE TABLE `casters` (
  `id_caster` int(11) NOT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `canal_origen` varchar(100) DEFAULT NULL,
  `estilo_narrativo` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de casters: nombre, canal de origen y estilo narrativo (metadata editorial).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `descargas_jobs`
--

CREATE TABLE `descargas_jobs` (
  `id_job` bigint(20) NOT NULL,
  `id_partida` int(11) NOT NULL,
  `estado` varchar(32) NOT NULL DEFAULT 'EN_COLA',
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp(),
  `iniciado_en` datetime DEFAULT NULL,
  `finalizado_en` datetime DEFAULT NULL,
  `log_path` text DEFAULT NULL,
  `error` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Cola/historial de jobs de descarga de video por partida: estado, timestamps, logs y error.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `draft_events`
--

CREATE TABLE `draft_events` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) NOT NULL,
  `ord` tinyint(4) NOT NULL,
  `is_pick` tinyint(1) NOT NULL,
  `team` enum('radiant','dire') NOT NULL,
  `hero_id` int(11) NOT NULL,
  `t_seg` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Eventos del draft (picks/bans) por match: orden, equipo, héroe y tiempo aproximado.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `equipos`
--

CREATE TABLE `equipos` (
  `id_equipo` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `opendota_team_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de equipos: nombre y referencia opcional a OpenDota team_id.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `equipo_aliases`
--

CREATE TABLE `equipo_aliases` (
  `id_alias` int(11) NOT NULL,
  `alias_nombre` varchar(255) NOT NULL,
  `id_equipo` int(11) NOT NULL,
  `fuente` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Alias alternativos para equipos (normalización de nombres). Un alias apunta a un equipo y una fuente.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `eventos`
--

CREATE TABLE `eventos` (
  `id_evento` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `anio` year(4) DEFAULT NULL,
  `opendota_league_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de eventos/ligas/torneos: nombre, año y referencia opcional a OpenDota league_id.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `eventos_juego`
--

CREATE TABLE `eventos_juego` (
  `id_evento` int(11) NOT NULL,
  `id_partida` int(11) DEFAULT NULL,
  `timestamp_evento` time DEFAULT NULL,
  `tipo_evento` varchar(50) DEFAULT NULL,
  `descripcion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Eventos manuales o simples asociados a una partida (timestamp, tipo y descripción).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `eventos_partida`
--

CREATE TABLE `eventos_partida` (
  `id_evento` bigint(20) NOT NULL,
  `match_id` int(11) NOT NULL,
  `t_seg` int(11) DEFAULT NULL,
  `tipo` varchar(32) DEFAULT NULL,
  `actor_slot` int(11) DEFAULT NULL,
  `target_slot` int(11) DEFAULT NULL,
  `actor_hero_id` int(11) DEFAULT NULL,
  `target_hero_id` int(11) DEFAULT NULL,
  `x` int(11) DEFAULT NULL,
  `y` int(11) DEFAULT NULL,
  `valor` varchar(128) DEFAULT NULL,
  `details_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`details_json`)),
  `event_hash` binary(16) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Eventos estructurados por partida (kills, torres, etc.). Incluye posición, actor/target, tipo y JSON de detalles.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `evento_alias`
--

CREATE TABLE `evento_alias` (
  `id_alias` int(11) NOT NULL,
  `id_evento` int(11) NOT NULL,
  `alias_nombre` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Alias alternativos para eventos/torneos (normalización).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `frases_modelo`
--

CREATE TABLE `frases_modelo` (
  `id_frase` int(11) NOT NULL,
  `tipo_evento` varchar(50) DEFAULT NULL,
  `emocion` varchar(50) DEFAULT NULL,
  `texto_generado` text DEFAULT NULL,
  `fuente` varchar(100) DEFAULT NULL,
  `calidad` int(11) DEFAULT 5
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='[IA] Dataset de entrenamiento/curación. Contiene el "vocabulario" emocional del Monstruo calificado por calidad para evitar alucinaciones.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `hitos_catalogo`
--

CREATE TABLE `hitos_catalogo` (
  `id_hito_tipo` int(11) NOT NULL,
  `slug` varchar(50) NOT NULL,
  `categoria` enum('DRAFT','COMBAT','ECONOMY','OBJECTIVE','SOCIAL') DEFAULT NULL,
  `polaridad` enum('POSITIVE','NEGATIVE','NEUTRAL') DEFAULT 'NEUTRAL',
  `severidad` enum('LOW','MEDIUM','HIGH','CRITICAL') DEFAULT NULL,
  `descripcion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Catálogo de hitos narrativos (tipos): categoría, polaridad, severidad y descripción para guiar generación de narrativa.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `matches`
--

CREATE TABLE `matches` (
  `id_match` int(11) NOT NULL,
  `id_serie` int(11) NOT NULL,
  `game_number` tinyint(4) DEFAULT NULL,
  `match_id_dota` bigint(20) UNSIGNED DEFAULT NULL,
  `duracion_texto` varchar(50) DEFAULT NULL,
  `resultado_mapa` varchar(100) DEFAULT NULL,
  `idioma` varchar(16) DEFAULT NULL,
  `fuente_api` varchar(32) NOT NULL DEFAULT 'OpenDota',
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp(),
  `actualizado_en` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Matches normalizados dentro de una serie: game_number, match_id_dota, resultado, idioma y fuente.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_chat_events`
--

CREATE TABLE `match_chat_events` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) DEFAULT NULL,
  `t_seconds` int(11) DEFAULT NULL,
  `from_hero_id` int(11) DEFAULT NULL,
  `to_hero_id` int(11) DEFAULT NULL,
  `message` text DEFAULT NULL,
  `is_radiant` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Eventos de chat dentro del match (all chat / team chat) con tiempo, héroes y mensaje.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_core`
--

CREATE TABLE `match_core` (
  `match_id` int(11) NOT NULL,
  `match_id_dota` bigint(20) NOT NULL,
  `duration_seconds` int(11) DEFAULT NULL,
  `start_time_utc` datetime DEFAULT NULL,
  `did_radiant_win` tinyint(1) DEFAULT NULL,
  `game_mode` varchar(32) DEFAULT NULL,
  `lobby_type` varchar(32) DEFAULT NULL,
  `region_id` int(11) DEFAULT NULL,
  `cluster_id` int(11) DEFAULT NULL,
  `league_id` bigint(20) DEFAULT NULL,
  `league_name` varchar(255) DEFAULT NULL,
  `radiant_team_id` bigint(20) DEFAULT NULL,
  `radiant_team_name` varchar(255) DEFAULT NULL,
  `dire_team_id` bigint(20) DEFAULT NULL,
  `dire_team_name` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Resumen core del match desde fuente externa (OpenDota): duración, start_time_utc, ganador, modo, liga y equipos.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_death_events`
--

CREATE TABLE `match_death_events` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) DEFAULT NULL,
  `t_seconds` int(11) DEFAULT NULL,
  `victim_slot` int(11) DEFAULT NULL,
  `gold_fed` int(11) DEFAULT NULL,
  `xp_fed` int(11) DEFAULT NULL,
  `pos_x` int(11) DEFAULT NULL,
  `pos_y` int(11) DEFAULT NULL,
  `is_dieback` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Eventos de muerte por match: víctima (slot), oro/xp cedido, posición y dieback.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_kill_events`
--

CREATE TABLE `match_kill_events` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) DEFAULT NULL,
  `t_seconds` int(11) DEFAULT NULL,
  `killer_slot` int(11) DEFAULT NULL,
  `target_hero_id` int(11) DEFAULT NULL,
  `gold` int(11) DEFAULT NULL,
  `xp` int(11) DEFAULT NULL,
  `pos_x` int(11) DEFAULT NULL,
  `pos_y` int(11) DEFAULT NULL,
  `is_solo` tinyint(1) DEFAULT NULL,
  `is_gank` tinyint(1) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Eventos de kill por match: killer slot, héroe objetivo, oro/xp, posición y flags (solo/gank).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_players`
--

CREATE TABLE `match_players` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) NOT NULL,
  `player_slot` int(11) DEFAULT NULL,
  `hero_id` int(11) DEFAULT NULL,
  `is_radiant` tinyint(1) DEFAULT NULL,
  `kills` int(11) DEFAULT NULL,
  `deaths` int(11) DEFAULT NULL,
  `assists` int(11) DEFAULT NULL,
  `networth` int(11) DEFAULT NULL,
  `hero_damage` int(11) DEFAULT NULL,
  `tower_damage` int(11) DEFAULT NULL,
  `level` int(11) DEFAULT NULL,
  `item0_id` int(11) DEFAULT NULL,
  `item1_id` int(11) DEFAULT NULL,
  `item2_id` int(11) DEFAULT NULL,
  `item3_id` int(11) DEFAULT NULL,
  `item4_id` int(11) DEFAULT NULL,
  `item5_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Stats finales por jugador (slot) en el match: K/D/A, networth, daño, items, etc.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_raw_json`
--

CREATE TABLE `match_raw_json` (
  `match_id` int(11) NOT NULL,
  `match_id_dota` bigint(20) NOT NULL,
  `json_data` longtext NOT NULL,
  `fetched_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Persistencia del JSON crudo del match (fuente API) para trazabilidad y reprocesos.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_snapshots`
--

CREATE TABLE `match_snapshots` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) DEFAULT NULL,
  `player_slot` int(11) DEFAULT NULL,
  `t_seconds` int(11) DEFAULT NULL,
  `metric` varchar(32) DEFAULT NULL,
  `value` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='[ANALÍTICA] Serie temporal de métricas por jugador (t_seconds in-game). Base para generar gráficos de ventaja y narrativa de remontadas.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_tower_deaths`
--

CREATE TABLE `match_tower_deaths` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) DEFAULT NULL,
  `t_seconds` int(11) DEFAULT NULL,
  `npc_id` int(11) DEFAULT NULL,
  `is_radiant` tinyint(1) DEFAULT NULL,
  `attacker` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Eventos de caída de torres por match: npc, bando y atacante.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `match_win_probability_raw`
--

CREATE TABLE `match_win_probability_raw` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) DEFAULT NULL,
  `t_seconds` int(11) DEFAULT NULL,
  `radiant_win_chance` float DEFAULT NULL,
  `source` varchar(32) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Win probability cruda por tiempo (t_seconds) desde modelo/fuente externa.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `partidas`
--

CREATE TABLE `partidas` (
  `id_partida` int(11) NOT NULL,
  `match_id_dota` bigint(20) UNSIGNED DEFAULT NULL,
  `evento` varchar(255) DEFAULT NULL,
  `fase` varchar(100) DEFAULT NULL,
  `equipos` varchar(255) DEFAULT NULL,
  `resultado` varchar(100) DEFAULT NULL,
  `duracion` varchar(50) DEFAULT NULL,
  `anio` year(4) DEFAULT NULL,
  `caster` varchar(255) DEFAULT NULL,
  `canal` varchar(255) DEFAULT NULL,
  `url_video` text DEFAULT NULL,
  `comentarios` text DEFAULT NULL,
  `video_descargado` tinyint(4) DEFAULT 0,
  `ruta_video` text DEFAULT NULL,
  `ts_inicio_video` datetime DEFAULT NULL,
  `ts_fin_video` datetime DEFAULT NULL,
  `whisper_json_path` text DEFAULT NULL,
  `idioma` varchar(16) DEFAULT NULL,
  `fuente_api` varchar(32) NOT NULL DEFAULT 'OpenDota',
  `video_platform` varchar(32) DEFAULT NULL,
  `video_channel` varchar(128) DEFAULT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp(),
  `actualizado_en` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `validado` tinyint(1) NOT NULL DEFAULT 1,
  `motivo_invalidez` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='[CORE] Registro maestro del pipeline. Vincula el ID de Valve con el archivo de video, estado de Whisper y validación final para casteo.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `partidas_map`
--

CREATE TABLE `partidas_map` (
  `id_partida` int(11) NOT NULL,
  `id_evento` int(11) DEFAULT NULL,
  `id_serie` int(11) DEFAULT NULL,
  `id_match` int(11) DEFAULT NULL,
  `id_video` int(11) DEFAULT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Mapa de relaciones entre partida y entidades normalizadas (evento/serie/match/video).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `partidas_meta`
--

CREATE TABLE `partidas_meta` (
  `match_id` int(11) NOT NULL,
  `match_id_dota` bigint(20) UNSIGNED DEFAULT NULL,
  `duration_s` int(11) DEFAULT NULL,
  `start_time_utc` datetime DEFAULT NULL,
  `radiant_win` tinyint(1) DEFAULT NULL,
  `patch` varchar(16) DEFAULT NULL,
  `game_mode` varchar(32) DEFAULT NULL,
  `lobby_type` varchar(32) DEFAULT NULL,
  `cluster` int(11) DEFAULT NULL,
  `region` int(11) DEFAULT NULL,
  `avg_mmr` int(11) DEFAULT NULL,
  `avg_rank_tier` int(11) DEFAULT NULL,
  `replay_url` text DEFAULT NULL,
  `league_id` bigint(20) DEFAULT NULL,
  `league_name` varchar(128) DEFAULT NULL,
  `radiant_team_id` bigint(20) DEFAULT NULL,
  `radiant_team_name` varchar(128) DEFAULT NULL,
  `dire_team_id` bigint(20) DEFAULT NULL,
  `dire_team_name` varchar(128) DEFAULT NULL,
  `enriched_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Metadatos enriquecidos de partida (patch, mmr, league, equipos, replay_url) con timestamp de enriquecimiento.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `player_match_stats`
--

CREATE TABLE `player_match_stats` (
  `match_id` int(11) NOT NULL,
  `slot` int(11) NOT NULL,
  `hero_id` int(11) NOT NULL,
  `lane` int(11) DEFAULT NULL,
  `role` int(11) DEFAULT NULL,
  `gpm` int(11) DEFAULT NULL,
  `xpm` int(11) DEFAULT NULL,
  `networth_end` int(11) DEFAULT NULL,
  `k` int(11) DEFAULT NULL,
  `d` int(11) DEFAULT NULL,
  `a` int(11) DEFAULT NULL,
  `last_hits` int(11) DEFAULT NULL,
  `denies` int(11) DEFAULT NULL,
  `damage` int(11) DEFAULT NULL,
  `heal` int(11) DEFAULT NULL,
  `items_json` longtext DEFAULT NULL,
  `skills_json` longtext DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Stats avanzados por jugador/slot en la partida (lane/role/gpm/xpm/items/skills en JSON).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `segmentos_audio`
--

CREATE TABLE `segmentos_audio` (
  `id_segmento` int(11) NOT NULL,
  `id_partida` int(11) DEFAULT NULL,
  `timestamp_inicio` time DEFAULT NULL,
  `timestamp_fin` time DEFAULT NULL,
  `texto` text DEFAULT NULL,
  `emocion` varchar(50) DEFAULT NULL,
  `tipo_evento` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Segmentos de audio/texto por partida (inicio/fin, texto, emoción y tipo_evento) para narración y alineación.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `segmentos_por_caster`
--

CREATE TABLE `segmentos_por_caster` (
  `id_segmento` int(11) DEFAULT NULL,
  `id_caster` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Relación N a N entre segmentos_audio y casters (quién narra qué segmento).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `series`
--

CREATE TABLE `series` (
  `id_serie` int(11) NOT NULL,
  `id_evento` int(11) NOT NULL,
  `fase` varchar(100) DEFAULT NULL,
  `id_equipo_a` int(11) DEFAULT NULL,
  `id_equipo_b` int(11) DEFAULT NULL,
  `best_of` tinyint(4) DEFAULT NULL,
  `ganador` varchar(255) DEFAULT NULL,
  `resultado_serie` varchar(50) DEFAULT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `snapshots_partida`
--

CREATE TABLE `snapshots_partida` (
  `id_snapshot` bigint(20) NOT NULL,
  `match_id` int(11) NOT NULL,
  `t_seg` int(11) NOT NULL,
  `metric` varchar(32) NOT NULL,
  `slot` int(11) NOT NULL,
  `value` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Snapshots por slot y métrica a nivel partida (t_seg) para timeline de narrativa/analítica.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `team_intenciones`
--

CREATE TABLE `team_intenciones` (
  `id_intencion` int(11) NOT NULL,
  `id_rol` int(11) DEFAULT NULL,
  `id_hito_tipo` int(11) DEFAULT NULL,
  `intencion_narrativa` varchar(100) DEFAULT NULL,
  `prompt_base` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Intenciones narrativas por rol y tipo de hito: texto de intención y prompt base para el generador.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `team_roles`
--

CREATE TABLE `team_roles` (
  `id_rol` int(11) NOT NULL,
  `nombre_clave` varchar(50) NOT NULL,
  `nombre_real` varchar(100) DEFAULT NULL,
  `tipo_rol` enum('MAIN_CASTER','ANALYST','PRODUCTION_CAM','DIRECTOR_IA','COMMUNITY_MANAGER','IRREVERENT_EXTRA') NOT NULL,
  `acento_region` varchar(50) DEFAULT NULL,
  `lore_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`lore_json`)),
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Roles/personajes del “caster studio”: tipo de rol, acento, lore JSON y flag activo.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `transcripciones`
--

CREATE TABLE `transcripciones` (
  `id` int(11) NOT NULL,
  `id_partida` int(11) DEFAULT NULL,
  `texto` longtext DEFAULT NULL,
  `calidad_audio` varchar(50) DEFAULT NULL,
  `numero_locutores` int(11) DEFAULT NULL,
  `fecha_procesado` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Transcripción final por partida (texto + metadata de calidad/locutores + fecha_procesado).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `transcripciones_bk`
--

CREATE TABLE `transcripciones_bk` (
  `id` int(11) NOT NULL DEFAULT 0,
  `id_partida` int(11) DEFAULT NULL,
  `texto` longtext DEFAULT NULL,
  `calidad_audio` varchar(50) DEFAULT NULL,
  `numero_locutores` int(11) DEFAULT NULL,
  `fecha_procesado` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Backup/tabla espejo de transcripciones (histórico o respaldo manual).';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `videos`
--

CREATE TABLE `videos` (
  `id_video` int(11) NOT NULL,
  `id_match` int(11) NOT NULL,
  `plataforma` varchar(32) DEFAULT NULL,
  `canal_video` varchar(128) DEFAULT NULL,
  `url_video` text DEFAULT NULL,
  `ruta_video` text DEFAULT NULL,
  `ts_inicio_video` datetime DEFAULT NULL,
  `ts_fin_video` datetime DEFAULT NULL,
  `video_descargado` tinyint(4) DEFAULT 0,
  `whisper_json_path` text DEFAULT NULL,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp(),
  `actualizado_en` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Videos normalizados por match: plataforma, canal, url/ruta, timestamps de recorte, estado descarga y whisper json path.';

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_json_sin_segmentos`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_json_sin_segmentos` (
`id_partida` int(11)
,`whisper_json_path` text
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_partidas_ids`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_partidas_ids` (
`id_local` int(11)
,`id_dota` bigint(20) unsigned
,`evento` varchar(255)
,`fase` varchar(100)
,`equipos` varchar(255)
,`resultado` varchar(100)
,`duracion` varchar(50)
,`anio` year(4)
,`caster` varchar(255)
,`canal` varchar(255)
,`url_video` text
,`video_descargado` tinyint(4)
,`ruta_video` text
,`ts_inicio_video` datetime
,`ts_fin_video` datetime
,`whisper_json_path` text
,`idioma` varchar(16)
,`fuente_api` varchar(32)
,`creado_en` timestamp
,`actualizado_en` timestamp
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_partidas_sin_json`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_partidas_sin_json` (
`id_partida` int(11)
,`ruta_video` text
);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `whisper_segments`
--

CREATE TABLE `whisper_segments` (
  `id_segmento` bigint(20) NOT NULL,
  `match_id` int(11) NOT NULL,
  `segment_id` int(11) NOT NULL,
  `t_inicio` decimal(8,3) DEFAULT NULL,
  `t_fin` decimal(8,3) DEFAULT NULL,
  `texto` text DEFAULT NULL,
  `avg_logprob` decimal(6,3) DEFAULT NULL,
  `compression_ratio` decimal(6,3) DEFAULT NULL,
  `no_speech_prob` decimal(6,3) DEFAULT NULL,
  `words_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`words_json`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Segmentos del Whisper por partida: tiempos, texto y métricas (logprob, ratios) + words_json.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `whisper_segments_bk`
--

CREATE TABLE `whisper_segments_bk` (
  `id_segmento` bigint(20) NOT NULL DEFAULT 0,
  `match_id` int(11) NOT NULL,
  `segment_id` int(11) NOT NULL,
  `t_inicio` decimal(8,3) DEFAULT NULL,
  `t_fin` decimal(8,3) DEFAULT NULL,
  `texto` text DEFAULT NULL,
  `avg_logprob` decimal(6,3) DEFAULT NULL,
  `compression_ratio` decimal(6,3) DEFAULT NULL,
  `no_speech_prob` decimal(6,3) DEFAULT NULL,
  `words_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`words_json`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Backup/tabla espejo de whisper_segments.';

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `winprob_timeline`
--

CREATE TABLE `winprob_timeline` (
  `id` bigint(20) NOT NULL,
  `match_id` int(11) NOT NULL,
  `t_seg` int(11) NOT NULL,
  `radiant_winprob` decimal(5,4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='Timeline de probabilidad de victoria (radiant) por segundo (t_seg) a nivel partida.';

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `alineaciones_evento_segmento`
--
ALTER TABLE `alineaciones_evento_segmento`
  ADD PRIMARY KEY (`id_alineacion`),
  ADD KEY `idx_align_match` (`match_id`);

--
-- Indices de la tabla `canales`
--
ALTER TABLE `canales`
  ADD PRIMARY KEY (`id_canal`),
  ADD UNIQUE KEY `uq_canal_nombre` (`nombre`);

--
-- Indices de la tabla `casters`
--
ALTER TABLE `casters`
  ADD PRIMARY KEY (`id_caster`);

--
-- Indices de la tabla `descargas_jobs`
--
ALTER TABLE `descargas_jobs`
  ADD PRIMARY KEY (`id_job`),
  ADD KEY `idx_jobs_partida` (`id_partida`),
  ADD KEY `idx_jobs_estado` (`estado`);

--
-- Indices de la tabla `draft_events`
--
ALTER TABLE `draft_events`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_draft_match` (`match_id`);

--
-- Indices de la tabla `equipos`
--
ALTER TABLE `equipos`
  ADD PRIMARY KEY (`id_equipo`),
  ADD UNIQUE KEY `uq_equipo_nombre` (`nombre`);

--
-- Indices de la tabla `equipo_aliases`
--
ALTER TABLE `equipo_aliases`
  ADD PRIMARY KEY (`id_alias`),
  ADD UNIQUE KEY `uq_alias` (`alias_nombre`),
  ADD KEY `fk_alias_equipo` (`id_equipo`);

--
-- Indices de la tabla `eventos`
--
ALTER TABLE `eventos`
  ADD PRIMARY KEY (`id_evento`),
  ADD UNIQUE KEY `uq_evento_nombre_anio` (`nombre`,`anio`);

--
-- Indices de la tabla `eventos_juego`
--
ALTER TABLE `eventos_juego`
  ADD PRIMARY KEY (`id_evento`),
  ADD KEY `id_partida` (`id_partida`);

--
-- Indices de la tabla `eventos_partida`
--
ALTER TABLE `eventos_partida`
  ADD PRIMARY KEY (`id_evento`),
  ADD UNIQUE KEY `uq_evt_hash` (`match_id`,`event_hash`),
  ADD KEY `idx_eventos_match_t` (`match_id`,`t_seg`),
  ADD KEY `idx_eventos_busqueda` (`match_id`,`t_seg`,`tipo`),
  ADD KEY `idx_evt_match_t` (`match_id`,`t_seg`),
  ADD KEY `idx_evt_match_tipo_t` (`match_id`,`tipo`,`t_seg`),
  ADD KEY `idx_evt_match_actor_t` (`match_id`,`actor_slot`,`t_seg`);

--
-- Indices de la tabla `evento_alias`
--
ALTER TABLE `evento_alias`
  ADD PRIMARY KEY (`id_alias`),
  ADD UNIQUE KEY `uq_alias` (`alias_nombre`),
  ADD KEY `id_evento` (`id_evento`);

--
-- Indices de la tabla `frases_modelo`
--
ALTER TABLE `frases_modelo`
  ADD PRIMARY KEY (`id_frase`);

--
-- Indices de la tabla `hitos_catalogo`
--
ALTER TABLE `hitos_catalogo`
  ADD PRIMARY KEY (`id_hito_tipo`),
  ADD UNIQUE KEY `slug` (`slug`),
  ADD UNIQUE KEY `uq_hito_slug` (`slug`),
  ADD KEY `idx_hito_cat` (`categoria`),
  ADD KEY `idx_hito_pol` (`polaridad`),
  ADD KEY `idx_hito_sev` (`severidad`);

--
-- Indices de la tabla `matches`
--
ALTER TABLE `matches`
  ADD PRIMARY KEY (`id_match`),
  ADD UNIQUE KEY `uq_match_unique` (`id_serie`,`game_number`),
  ADD UNIQUE KEY `uq_serie_game` (`id_serie`,`game_number`),
  ADD KEY `idx_match_id_dota` (`match_id_dota`);

--
-- Indices de la tabla `match_chat_events`
--
ALTER TABLE `match_chat_events`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_match_time` (`match_id`,`t_seconds`);

--
-- Indices de la tabla `match_core`
--
ALTER TABLE `match_core`
  ADD PRIMARY KEY (`match_id`);

--
-- Indices de la tabla `match_death_events`
--
ALTER TABLE `match_death_events`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_match_time` (`match_id`,`t_seconds`);

--
-- Indices de la tabla `match_kill_events`
--
ALTER TABLE `match_kill_events`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_match_time` (`match_id`,`t_seconds`);

--
-- Indices de la tabla `match_players`
--
ALTER TABLE `match_players`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_match_player` (`match_id`,`player_slot`);

--
-- Indices de la tabla `match_raw_json`
--
ALTER TABLE `match_raw_json`
  ADD PRIMARY KEY (`match_id`);

--
-- Indices de la tabla `match_snapshots`
--
ALTER TABLE `match_snapshots`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_snap` (`match_id`,`player_slot`,`t_seconds`,`metric`),
  ADD KEY `idx_match_time` (`match_id`,`t_seconds`);

--
-- Indices de la tabla `match_tower_deaths`
--
ALTER TABLE `match_tower_deaths`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_match_time` (`match_id`,`t_seconds`);

--
-- Indices de la tabla `match_win_probability_raw`
--
ALTER TABLE `match_win_probability_raw`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_match_time` (`match_id`,`t_seconds`);

--
-- Indices de la tabla `partidas`
--
ALTER TABLE `partidas`
  ADD PRIMARY KEY (`id_partida`),
  ADD UNIQUE KEY `uq_partidas_match_id_dota` (`match_id_dota`),
  ADD KEY `idx_partidas_descarga` (`video_descargado`),
  ADD KEY `idx_partidas_ruta` (`ruta_video`(255)),
  ADD KEY `idx_partidas_match_id_dota_nullsafe` (`match_id_dota`),
  ADD KEY `idx_partidas_ts_inicio` (`ts_inicio_video`),
  ADD KEY `idx_partidas_ts_fin` (`ts_fin_video`),
  ADD KEY `idx_partidas_json_path` (`whisper_json_path`(255));

--
-- Indices de la tabla `partidas_map`
--
ALTER TABLE `partidas_map`
  ADD PRIMARY KEY (`id_partida`),
  ADD KEY `fk_map_evento` (`id_evento`),
  ADD KEY `fk_map_serie` (`id_serie`),
  ADD KEY `fk_map_match` (`id_match`),
  ADD KEY `fk_map_video` (`id_video`);

--
-- Indices de la tabla `partidas_meta`
--
ALTER TABLE `partidas_meta`
  ADD PRIMARY KEY (`match_id`),
  ADD KEY `idx_pm_match_id_dota` (`match_id_dota`),
  ADD KEY `idx_pm_start_time` (`start_time_utc`);

--
-- Indices de la tabla `player_match_stats`
--
ALTER TABLE `player_match_stats`
  ADD PRIMARY KEY (`match_id`,`slot`);

--
-- Indices de la tabla `segmentos_audio`
--
ALTER TABLE `segmentos_audio`
  ADD PRIMARY KEY (`id_segmento`),
  ADD KEY `id_partida` (`id_partida`);

--
-- Indices de la tabla `segmentos_por_caster`
--
ALTER TABLE `segmentos_por_caster`
  ADD KEY `id_segmento` (`id_segmento`),
  ADD KEY `id_caster` (`id_caster`);

--
-- Indices de la tabla `series`
--
ALTER TABLE `series`
  ADD PRIMARY KEY (`id_serie`),
  ADD UNIQUE KEY `uq_serie` (`id_evento`,`fase`,`id_equipo_a`,`id_equipo_b`),
  ADD KEY `fk_series_a` (`id_equipo_a`),
  ADD KEY `fk_series_b` (`id_equipo_b`);

--
-- Indices de la tabla `snapshots_partida`
--
ALTER TABLE `snapshots_partida`
  ADD PRIMARY KEY (`id_snapshot`),
  ADD UNIQUE KEY `uq_snap_point` (`match_id`,`t_seg`,`metric`,`slot`),
  ADD KEY `idx_snap_match_t` (`match_id`,`t_seg`),
  ADD KEY `idx_snap_busqueda` (`match_id`,`t_seg`,`metric`,`slot`),
  ADD KEY `idx_snap_match_metric_t` (`match_id`,`metric`,`t_seg`),
  ADD KEY `idx_snap_match_slot_metric_t` (`match_id`,`slot`,`metric`,`t_seg`);

--
-- Indices de la tabla `team_intenciones`
--
ALTER TABLE `team_intenciones`
  ADD PRIMARY KEY (`id_intencion`),
  ADD UNIQUE KEY `uq_intencion` (`id_rol`,`id_hito_tipo`),
  ADD KEY `idx_int_rol` (`id_rol`),
  ADD KEY `idx_int_hito` (`id_hito_tipo`);

--
-- Indices de la tabla `team_roles`
--
ALTER TABLE `team_roles`
  ADD PRIMARY KEY (`id_rol`),
  ADD UNIQUE KEY `nombre_clave` (`nombre_clave`),
  ADD UNIQUE KEY `uq_team_nombre` (`nombre_clave`),
  ADD KEY `idx_team_tipo` (`tipo_rol`),
  ADD KEY `idx_team_activo` (`activo`);

--
-- Indices de la tabla `transcripciones`
--
ALTER TABLE `transcripciones`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_transcripcion_por_partida` (`id_partida`);

--
-- Indices de la tabla `videos`
--
ALTER TABLE `videos`
  ADD PRIMARY KEY (`id_video`),
  ADD KEY `fk_videos_match` (`id_match`);

--
-- Indices de la tabla `whisper_segments`
--
ALTER TABLE `whisper_segments`
  ADD PRIMARY KEY (`id_segmento`),
  ADD UNIQUE KEY `uq_ws_match_segment` (`match_id`,`segment_id`),
  ADD KEY `idx_ws_match` (`match_id`);

--
-- Indices de la tabla `winprob_timeline`
--
ALTER TABLE `winprob_timeline`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_wpt_match` (`match_id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `alineaciones_evento_segmento`
--
ALTER TABLE `alineaciones_evento_segmento`
  MODIFY `id_alineacion` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `canales`
--
ALTER TABLE `canales`
  MODIFY `id_canal` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `casters`
--
ALTER TABLE `casters`
  MODIFY `id_caster` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `descargas_jobs`
--
ALTER TABLE `descargas_jobs`
  MODIFY `id_job` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `draft_events`
--
ALTER TABLE `draft_events`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `equipos`
--
ALTER TABLE `equipos`
  MODIFY `id_equipo` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `equipo_aliases`
--
ALTER TABLE `equipo_aliases`
  MODIFY `id_alias` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `eventos`
--
ALTER TABLE `eventos`
  MODIFY `id_evento` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `eventos_juego`
--
ALTER TABLE `eventos_juego`
  MODIFY `id_evento` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `eventos_partida`
--
ALTER TABLE `eventos_partida`
  MODIFY `id_evento` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `evento_alias`
--
ALTER TABLE `evento_alias`
  MODIFY `id_alias` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `frases_modelo`
--
ALTER TABLE `frases_modelo`
  MODIFY `id_frase` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `hitos_catalogo`
--
ALTER TABLE `hitos_catalogo`
  MODIFY `id_hito_tipo` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `matches`
--
ALTER TABLE `matches`
  MODIFY `id_match` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `match_chat_events`
--
ALTER TABLE `match_chat_events`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `match_death_events`
--
ALTER TABLE `match_death_events`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `match_kill_events`
--
ALTER TABLE `match_kill_events`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `match_players`
--
ALTER TABLE `match_players`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `match_snapshots`
--
ALTER TABLE `match_snapshots`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `match_tower_deaths`
--
ALTER TABLE `match_tower_deaths`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `match_win_probability_raw`
--
ALTER TABLE `match_win_probability_raw`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `partidas`
--
ALTER TABLE `partidas`
  MODIFY `id_partida` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `segmentos_audio`
--
ALTER TABLE `segmentos_audio`
  MODIFY `id_segmento` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `series`
--
ALTER TABLE `series`
  MODIFY `id_serie` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `snapshots_partida`
--
ALTER TABLE `snapshots_partida`
  MODIFY `id_snapshot` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `team_intenciones`
--
ALTER TABLE `team_intenciones`
  MODIFY `id_intencion` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `team_roles`
--
ALTER TABLE `team_roles`
  MODIFY `id_rol` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `transcripciones`
--
ALTER TABLE `transcripciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `videos`
--
ALTER TABLE `videos`
  MODIFY `id_video` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `whisper_segments`
--
ALTER TABLE `whisper_segments`
  MODIFY `id_segmento` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `winprob_timeline`
--
ALTER TABLE `winprob_timeline`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_json_sin_segmentos`
--
DROP TABLE IF EXISTS `v_json_sin_segmentos`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `v_json_sin_segmentos`  AS SELECT `p`.`id_partida` AS `id_partida`, `p`.`whisper_json_path` AS `whisper_json_path` FROM (`partidas` `p` left join `whisper_segments` `ws` on(`ws`.`match_id` = `p`.`id_partida`)) WHERE `p`.`whisper_json_path` is not null GROUP BY `p`.`id_partida`, `p`.`whisper_json_path` HAVING count(`ws`.`id_segmento`) = 0 ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_partidas_ids`
--
DROP TABLE IF EXISTS `v_partidas_ids`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `v_partidas_ids`  AS SELECT `p`.`id_partida` AS `id_local`, `p`.`match_id_dota` AS `id_dota`, `p`.`evento` AS `evento`, `p`.`fase` AS `fase`, `p`.`equipos` AS `equipos`, `p`.`resultado` AS `resultado`, `p`.`duracion` AS `duracion`, `p`.`anio` AS `anio`, `p`.`caster` AS `caster`, `p`.`canal` AS `canal`, `p`.`url_video` AS `url_video`, `p`.`video_descargado` AS `video_descargado`, `p`.`ruta_video` AS `ruta_video`, `p`.`ts_inicio_video` AS `ts_inicio_video`, `p`.`ts_fin_video` AS `ts_fin_video`, `p`.`whisper_json_path` AS `whisper_json_path`, `p`.`idioma` AS `idioma`, `p`.`fuente_api` AS `fuente_api`, `p`.`creado_en` AS `creado_en`, `p`.`actualizado_en` AS `actualizado_en` FROM `partidas` AS `p` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_partidas_sin_json`
--
DROP TABLE IF EXISTS `v_partidas_sin_json`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `v_partidas_sin_json`  AS SELECT `partidas`.`id_partida` AS `id_partida`, `partidas`.`ruta_video` AS `ruta_video` FROM `partidas` WHERE `partidas`.`video_descargado` = 1 AND `partidas`.`ruta_video` is not null AND (`partidas`.`whisper_json_path` is null OR `partidas`.`whisper_json_path` = '') ;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `alineaciones_evento_segmento`
--
ALTER TABLE `alineaciones_evento_segmento`
  ADD CONSTRAINT `fk_align_partida` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `draft_events`
--
ALTER TABLE `draft_events`
  ADD CONSTRAINT `fk_draft_match` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `equipo_aliases`
--
ALTER TABLE `equipo_aliases`
  ADD CONSTRAINT `fk_alias_equipo` FOREIGN KEY (`id_equipo`) REFERENCES `equipos` (`id_equipo`);

--
-- Filtros para la tabla `eventos_juego`
--
ALTER TABLE `eventos_juego`
  ADD CONSTRAINT `eventos_juego_ibfk_1` FOREIGN KEY (`id_partida`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `eventos_partida`
--
ALTER TABLE `eventos_partida`
  ADD CONSTRAINT `fk_event_partida` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `evento_alias`
--
ALTER TABLE `evento_alias`
  ADD CONSTRAINT `evento_alias_ibfk_1` FOREIGN KEY (`id_evento`) REFERENCES `eventos` (`id_evento`);

--
-- Filtros para la tabla `matches`
--
ALTER TABLE `matches`
  ADD CONSTRAINT `fk_matches_serie` FOREIGN KEY (`id_serie`) REFERENCES `series` (`id_serie`);

--
-- Filtros para la tabla `partidas_map`
--
ALTER TABLE `partidas_map`
  ADD CONSTRAINT `fk_map_evento` FOREIGN KEY (`id_evento`) REFERENCES `eventos` (`id_evento`),
  ADD CONSTRAINT `fk_map_match` FOREIGN KEY (`id_match`) REFERENCES `matches` (`id_match`),
  ADD CONSTRAINT `fk_map_serie` FOREIGN KEY (`id_serie`) REFERENCES `series` (`id_serie`),
  ADD CONSTRAINT `fk_map_video` FOREIGN KEY (`id_video`) REFERENCES `videos` (`id_video`);

--
-- Filtros para la tabla `partidas_meta`
--
ALTER TABLE `partidas_meta`
  ADD CONSTRAINT `fk_meta_partida` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `player_match_stats`
--
ALTER TABLE `player_match_stats`
  ADD CONSTRAINT `fk_pms_match` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `segmentos_audio`
--
ALTER TABLE `segmentos_audio`
  ADD CONSTRAINT `segmentos_audio_ibfk_1` FOREIGN KEY (`id_partida`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `segmentos_por_caster`
--
ALTER TABLE `segmentos_por_caster`
  ADD CONSTRAINT `segmentos_por_caster_ibfk_1` FOREIGN KEY (`id_segmento`) REFERENCES `segmentos_audio` (`id_segmento`),
  ADD CONSTRAINT `segmentos_por_caster_ibfk_2` FOREIGN KEY (`id_caster`) REFERENCES `casters` (`id_caster`);

--
-- Filtros para la tabla `series`
--
ALTER TABLE `series`
  ADD CONSTRAINT `fk_series_a` FOREIGN KEY (`id_equipo_a`) REFERENCES `equipos` (`id_equipo`),
  ADD CONSTRAINT `fk_series_b` FOREIGN KEY (`id_equipo_b`) REFERENCES `equipos` (`id_equipo`),
  ADD CONSTRAINT `fk_series_evento` FOREIGN KEY (`id_evento`) REFERENCES `eventos` (`id_evento`);

--
-- Filtros para la tabla `snapshots_partida`
--
ALTER TABLE `snapshots_partida`
  ADD CONSTRAINT `fk_snap_partida` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `team_intenciones`
--
ALTER TABLE `team_intenciones`
  ADD CONSTRAINT `team_intenciones_ibfk_1` FOREIGN KEY (`id_rol`) REFERENCES `team_roles` (`id_rol`),
  ADD CONSTRAINT `team_intenciones_ibfk_2` FOREIGN KEY (`id_hito_tipo`) REFERENCES `hitos_catalogo` (`id_hito_tipo`);

--
-- Filtros para la tabla `transcripciones`
--
ALTER TABLE `transcripciones`
  ADD CONSTRAINT `transcripciones_ibfk_1` FOREIGN KEY (`id_partida`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `videos`
--
ALTER TABLE `videos`
  ADD CONSTRAINT `fk_videos_match` FOREIGN KEY (`id_match`) REFERENCES `matches` (`id_match`);

--
-- Filtros para la tabla `whisper_segments`
--
ALTER TABLE `whisper_segments`
  ADD CONSTRAINT `fk_ws_partida` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);

--
-- Filtros para la tabla `winprob_timeline`
--
ALTER TABLE `winprob_timeline`
  ADD CONSTRAINT `fk_wpt_match` FOREIGN KEY (`match_id`) REFERENCES `partidas` (`id_partida`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
