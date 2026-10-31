{{if:pre_production}}
{{config:project_name}} is pre-production. There are no production users, customer datasets, or deployed downstream state to preserve, and local development state (the local database, feature state, task-owned fixtures) is disposable. Do not treat backward compatibility, rollback or upgrade paths, backfills, deprecation periods, dual behavior, rollout machinery, or live-data migration as requirements unless direct authority names a concrete current consumer or retained non-disposable state. Weigh long-term fit only in a foundational architecture comparison that Iris has expressly routed.

This does not relax tenant isolation, authorization, secret handling, or destructive-action targeting. Those stay required wherever the capability touches them.
{{else}}
{{config:project_name}} is in production. Treat deployed behavior, stored data, and existing users as constraints to preserve unless direct authority says otherwise.

Tenant isolation, authorization, secret handling, and destructive-action targeting stay required wherever the capability touches them.
{{/if}}
