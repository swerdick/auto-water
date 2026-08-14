# Changelog

## [0.4.0](https://github.com/swerdick/yavanna/compare/v0.3.0...v0.4.0) (2026-08-14)


### Features

* **deploy:** archive yavanna-db to Backblaze B2 via the barman plugin ([#22](https://github.com/swerdick/yavanna/issues/22)) ([a3e9d4d](https://github.com/swerdick/yavanna/commit/a3e9d4da405e992bee227dbb60b548abbe3bef50))

## [0.3.0](https://github.com/swerdick/auto-water/compare/v0.2.0...v0.3.0) (2026-08-10)


### Features

* rename project to yavanna ([8323699](https://github.com/swerdick/auto-water/commit/83236991a577ca14ad76d81a6e3b81f3cc3a4ee6))

## [0.2.0](https://github.com/swerdick/auto-water/compare/v0.1.0...v0.2.0) (2026-08-10)


### Features

* add deploy/ manifests for Flux deployment on samwise ([9791712](https://github.com/swerdick/auto-water/commit/97917123ddd014f9170b851c763fbcd766caaf8e))
* add k8s deploy manifests for the Flux-synced deployment ([49a5ef5](https://github.com/swerdick/auto-water/commit/49a5ef5288e1bdf88cc04b7658cddaf7c1fb9cdc))
* ADS1115 soil moisture, DS18B20 plant naming, resilient sensor init ([6261075](https://github.com/swerdick/auto-water/commit/6261075ecff241c764099dfe082256836d74bb9f))
* big refactor back to github hosting, docker --&gt; podman, agent markdown files, justfile, and updating dependencies to work with pi5.  the project lives ([c993cee](https://github.com/swerdick/auto-water/commit/c993cee224dfed3452ea67351339e960f661680f))
* **deploy:** add Grafana dashboard for sensor readings ([d73908b](https://github.com/swerdick/auto-water/commit/d73908b9893e6a75f7f46003b532993ca8763afa))
* **deploy:** expose Postgres via MetalLB LoadBalancer ([8f3ca1d](https://github.com/swerdick/auto-water/commit/8f3ca1d4c6c2a26a56bd720b50c83eb327b3c755))
* **deploy:** expose Postgres via MetalLB LoadBalancer (192.168.1.221) ([645fbb4](https://github.com/swerdick/auto-water/commit/645fbb4d1fde5da6ac52e2a01a38043de138a0e2))
* **deploy:** Grafana dashboard for sensor readings ([b4d2513](https://github.com/swerdick/auto-water/commit/b4d25135c48517767e9ecded2a5aa3085865f168))
* enable db monitoring ([250e55f](https://github.com/swerdick/auto-water/commit/250e55ff7a4133b17149f78faf290b9ea9c113a9))
* replace Flask deploy-test with sensor-reading poller + inventory ([9cf5463](https://github.com/swerdick/auto-water/commit/9cf546368dc5944c135b442da1097f4025d02e45))
* spill the retry buffer to disk so restarts don't drop readings ([13ad2a6](https://github.com/swerdick/auto-water/commit/13ad2a6710eae34c62c9fefa5ac693b93e29bef4))
* split temperature panel by sensor; one timestamp per poll cycle ([7e2830f](https://github.com/swerdick/auto-water/commit/7e2830f89fac663ab7e7fa1f965a8f114d38ce70))
* split temperature panel by sensor; one timestamp per poll cycle ([92b06fd](https://github.com/swerdick/auto-water/commit/92b06fd24261095bdba4c9151a231c8179f751a8))
* time-based retry-buffer retention (30d) + pod memory limit ([928c338](https://github.com/swerdick/auto-water/commit/928c3383b94550c2997656ef528051646bf45f1e))
* time-based retry-buffer retention (30d) + pod memory limit ([4bddeb2](https://github.com/swerdick/auto-water/commit/4bddeb25b46242b2d0841acfa1b9e05dcf1619a2))


### Bug Fixes

* address Copilot PR review ([4076272](https://github.com/swerdick/auto-water/commit/4076272fcd1f11d466e5b94fa4097107dcf0f8dd))
* **container:** build lgpio from source for Blinka on Pi 5 ([b26705c](https://github.com/swerdick/auto-water/commit/b26705cdcb2e60015e8fb0aac794d56157c0988d))
* **container:** build lgpio from source for Blinka on Pi 5 ([ab50429](https://github.com/swerdick/auto-water/commit/ab50429a0103257b3592f913c2bbf5c6f120d30e))
* **deploy:** correct samwise toleration key ([aad9f23](https://github.com/swerdick/auto-water/commit/aad9f23c14f7da0f62e3ed1189827c45fd0ebcdf))
* **deploy:** correct samwise toleration key ([8e0f423](https://github.com/swerdick/auto-water/commit/8e0f42320d8e669455460c0a359883b99080785c))
* PR 16 review feedback ([b0fad69](https://github.com/swerdick/auto-water/commit/b0fad695aaf4c02f965463596f6c34770dbaf20e))


### Refactoring

* **deploy:** hand-manage CNPG PodMonitor (enablePodMonitor deprecated) ([f2bda7f](https://github.com/swerdick/auto-water/commit/f2bda7f435865b58fc9098a1f1d2cdd6e130fa6c))
* src-layout, DB migrations, and vibe-seeker-style CI/CD ([5e6340a](https://github.com/swerdick/auto-water/commit/5e6340a65a9255b78004df62c4cc6391cf5513e6))
* src-layout, DB migrations, and vibe-seeker-style CI/CD ([4b558cf](https://github.com/swerdick/auto-water/commit/4b558cfba04a19e04762d901e1693d33e589bc2c))


### Build & Dependencies

* **deps:** bump googleapis/release-please-action from 4 to 5 ([114e506](https://github.com/swerdick/auto-water/commit/114e506388f2f0b1762accf61a92c08b54c70f9b))
