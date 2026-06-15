# Metrics

Mattermost provides the following performance monitoring statistics to integrate with Prometheus and Grafana.

A Mattermost Entry, Enterprise, or Enterprise Advanced license is required to connect to the `/metrics` endpoint at port 8067 by default.

## API metrics

* **mattermost_api_time**: The total time in seconds to execute a given API handler.

## Caching metrics

* **mattermost_cache_etag_hit_total**: The total number of ETag cache hits for a specific cache.
* **mattermost_cache_etag_miss_total**: The total number of ETag cache misses for an API call.
* **mattermost_cache_mem_hit_total**: The total number of memory cache hits for a specific cache.
* **mattermost_cache_mem_invalidation_total**: The total number of memory cache invalidations for a specific cache.
* **mattermost_cache_mem_miss_total**: The total number of cache misses for a specific cache.

## Cluster metrics

* **mattermost_cluster_cluster_request_duration_seconds**: The total duration in seconds of the inter-node cluster requests.
* **mattermost_cluster_cluster_health_score**: A score that gives an idea of how well it is meeting the soft-real time requirements of the gossip protocol.
* **mattermost_cluster_cluster_requests_total**: The total number of inter-node requests.
* **mattermost_cluster_cluster_event_type_totals**: The total number of cluster requests sent for any type.

## Database metrics

* **mattermost_db_active_users**: The total number of active users.
* **mattermost_db_cache_time**: Time to execute the cache handler.
* **mattermost_db_master_connections_total**: The total number of connections to the master database.
* **mattermost_db_read_replica_connections_total**: The total number of connections to all the read replica databases.
* **mattermost_db_search_replica_connections_total**: The total number of connections to all the search replica databases.
* **mattermost_db_store_time**: The total time in seconds to execute a given database store method.
* **mattermost_db_replica_lag_abs**: Absolute lag time based on binlog distance/transaction queue length.
* **mattermost_db_replica_lag_time**: The time taken for the replica to catch up.

## Database connection metrics

* **go_sql_max_open_connections**: Maximum number of open connections to the database.
* **go_sql_open_connections**: The number of established connections both in use and idle.
* **go_sql_in_use_connections**: The number of connections currently in use.
* **go_sql_idle_connections**: The number of idle connections.
* **go_sql_wait_count_total**: The total number of connections waited for.
* **go_sql_wait_duration_seconds_total**: The total time blocked waiting for a new connection.
* **go_sql_max_idle_closed_total**: The total number of connections closed due to SetMaxIdleConns.
* **go_sql_max_idle_time_closed_total**: The total number of connections closed due to SetConnMaxIdleTime.
* **go_sql_max_lifetime_closed_total**: The total number of connections closed due to SetConnMaxLifetime.

## HTTP metrics

* **mattermost_http_errors_total**: The total number of http API errors.
* **mattermost_http_requests_total**: The total number of http API requests.
* **mattermost_http_websockets_total**: The total number of websocket connections to this server.

## Login and session metrics

* **mattermost_login_logins_fail_total**: The total number of failed logins.
* **mattermost_login_logins_total**: The total number of successful logins.

## Mattermost channels metrics

* **mattermost_post_broadcasts_total**: The total number of websocket broadcasts sent because a post was created.
* **mattermost_post_emails_sent_total**: The total number of emails sent because a post was created.
* **mattermost_post_file_attachments_total**: The total number of file attachments created because a post was created.
* **mattermost_post_pushes_sent_total**: The total number of mobile push notifications sent because a post was created.
* **mattermost_post_total**: The total number of posts created.
* **mattermost_post_webhooks_total**: Total number of webhook posts created.

## Process metrics

* **mattermost_process_cpu_seconds_total**: Total user and system CPU time spent in seconds.
* **mattermost_process_max_fds**: Maximum number of open file descriptors.
* **mattermost_process_open_fds**: Number of open file descriptors.
* **mattermost_process_resident_memory_bytes**: Resident memory size in bytes.
* **mattermost_process_start_time_seconds**: Start time of the process since unix epoch in seconds.
* **mattermost_process_virtual_memory_bytes**: Virtual memory size in bytes.
* **mattermost_process_virtual_memory_max_bytes**: Maximum amount of virtual memory available in bytes.

## Search metrics

* **mattermost_search_posts_searches_duration_seconds**: The total duration in seconds of post searches.
* **mattermost_search_channel_index_total**: The total number of channel indexes carried out.
* **mattermost_search_file_index_total**: The total number of files indexes carried out.
* **mattermost_search_files_searches_duration_seconds**: The total duration in seconds of file searches.
* **mattermost_search_files_searches_total**: The total number of file searches carried out.
* **mattermost_search_post_index_total**: The total number of posts indexes carried out.
* **mattermost_search_posts_searches_total**: The total number of post searches carried out.
* **mattermost_search_user_index_total**: The total number of user indexes carried out.
* **mattermost_search_engine_status**: Status of the configured search engine: 1 = healthy or not configured, 0 = configured but unavailable. Use this metric to set up alerts for search engine outages.

## WebSocket metrics

* **mattermost_websocket_broadcast_buffer_size**: Number of events in the websocket broadcasts buffer waiting to be processed.
* **mattermost_websocket_broadcast_buffer_users_registered**: Number of users registered in a broadcast buffer hub.
* **mattermost_websocket_broadcasts_total**: The total number of websocket broadcasts sent for any type.
* **mattermost_websocket_event_total**: Total number of websocket events.
* **mattermost_websocket_reconnects_total**: Total number of websocket reconnect attempts.

## Logging metrics

* **mattermost_logging_logger_queue_used**: Number of records in log target queue.
* **mattermost_logging_logger_logged_total**: The total number of records logged.
* **mattermost_logging_logger_error_total**: The total number of logger errors.
* **mattermost_logging_logger_dropped_total**: The total number of dropped log records.
* **mattermost_logging_logger_blocked_total**: The total number of log records that were blocked/delayed.

## Debugging metrics - system

* **mattermost_system_server_start_time**: The time the server started.

## Debugging metrics - jobs

* **mattermost_jobs_active**: Number of active jobs.

## Plugin metrics

* **mattermost_plugin_api_time**: Time to execute plugin API handlers in seconds.
* **mattermost_plugin_hook_time**: Time to execute plugin hook handler in seconds.
* **mattermost_plugin_multi_hook_server_time**: Time for the server to execute multiple plugin hook handlers in seconds.
* **mattermost_plugin_multi_hook_time**: Time to execute multiple plugin hook handler in seconds.

## Shared metrics

* **mattermost_shared_channels_sync_collection_duration_seconds**: Duration tasks spend collecting sync data (seconds).
* **mattermost_shared_channels_sync_collection_step_duration_seconds**: Duration tasks spend in each step collecting data (seconds).
* **mattermost_shared_channels_sync_count**: Count of sync events processed for each remote.
* **mattermost_shared_channels_sync_send_duration_seconds**: Duration tasks spend sending sync data (seconds).
* **mattermost_shared_channels_sync_send_step_duration_seconds**: Duration tasks spend in each step sending data (seconds).
* **mattermost_shared_channels_task_in_queue_duration_seconds**: Duration tasks spend in queue (seconds).
* **mattermost_shared_channels_task_queue_size**: Current number of tasks in queue.

## Remote cluster metrics

* **mattermost_remote_cluster_clock_skew**: An approximated value for clock skew between clusters.
* **mattermost_remote_cluster_conn_state_change_total**: Total number of connection state changes.
* **mattermost_remote_cluster_msg_errors_total**: Total number of message errors.
* **mattermost_remote_cluster_msg_received_total**: Total number of messages received from the remote cluster.
* **mattermost_remote_cluster_msg_sent_total**: Total number of messages sent to the remote cluster.
* **mattermost_remote_cluster_ping_time**: The ping roundtrip times to the remote cluster.

## Notification metrics

* **mattermost_notifications_error**: Total number of errors that stop the notification flow.
* **mattermost_notifications_not_sent**: Total number of notifications the system deliberately did not send.
* **mattermost_notifications_success**: Total number of successfully sent notifications.
* **mattermost_notifications_total**: Total number of notification events.
* **mattermost_notifications_total_ack**: Total number of notification events acknowledged.
* **mattermost_notifications_unsupported**: Total number of untrackable notifications due to an unsupported app version.

## Mobile app metrics

* **mattermost_mobileapp_mobile_channel_switch**: Duration of the time taken from when a user clicks on a channel name, and the full channel sreen is loaded (seconds).
* **mattermost_mobileapp_mobile_load**: Duration of the time taken from when a user opens the app and the app finally loads all relevant information (seconds).
* **mattermost_mobileapp_mobile_team_switch**: Duration of the time taken from when a user clicks on a team, and the full categories screen is loaded (seconds).

## Web app metrics

* **mattermost_webapp_channel_switch**: Duration of the time taken from when a user clicks on a channel in the LHS to when posts in that channel become visible (seconds).
* **mattermost_webapp_cumulative_layout_shift**: Measure of how much a page’s content shifts unexpectedly.
* **mattermost_webapp_first_contentful_paint**: Duration of how long it takes for any content to be displayed on screen to a user (seconds).
* **mattermost_webapp_global_threads_load**: Duration of the time taken from when a user clicks to open Threads in the LHS until when the global threads view becomes visible (milliseconds).
* **mattermost_webapp_interaction_to_next_paint**: Measure of how long it takes for a user to see the effects of clicking with a mouse, tapping with a touchscreen, or pressing a key on the keyboard (seconds).
* **mattermost_webapp_largest_contentful_paint**: Duration of how long it takes for large content to be displayed on screen to a user (seconds).
* **mattermost_webapp_long_tasks**: Counter of the number of times that the browser’s main UI thread is blocked for more than 50ms by a single task.
* **mattermost_webapp_page_load**: The amount of time from when the browser starts loading the web app until when the web app’s load event has finished (seconds).
* **mattermost_webapp_rhs_load**: Duration of the time taken from when a user clicks to open a thread in the RHS until when posts in that thread become visible (seconds).
* **mattermost_webapp_team_switch**: Duration of the time taken from when a user clicks on a team in the LHS to when posts in that team become visible (seconds).
* **mattermost_webapp_time_to_first_byte**: Duration from when a browser starts to request a page from a server until when it starts to receive data in response (seconds).

# Standard Go metrics

The performance monitoring feature provides standard Go metrics for HTTP server runtime profiling data and system monitoring. These metrics are available in every Mattermost plan.

* **go_memstats_alloc_bytes**: for memory usage.
* **go_goroutines**: for number of goroutines.
* **go_gc_duration_seconds**: for garbage collection duration.
* **go_memstats_heap_objects**: for object tracking on the heap.
