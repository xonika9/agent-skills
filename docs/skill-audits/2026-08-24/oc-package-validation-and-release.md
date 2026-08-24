# Пакетные проверки и выпуск версии `agent-skills`

- Дата проверки: 2026-08-24
- Область: пакетные проверки, метаданные плагинов и выпуск версии
- Статус: подтверждено по текущему рабочему каталогу и локальной истории Git
- Уверенность: высокая для логики репозитория; настройки защиты ветки GitHub не проверялись

## Итог

В репозитории есть два связанных контура. Workflow `Validate` выполняет автоматические проверки навыков, публичных данных, метаданных пакета и changelog. Отдельный локальный предрелизный набор шире CI и добавляет проверки глобальных инструкций, внешних валидаторов и установки пакета.

Версия хранится одновременно в Claude Code и Codex plugin-манифестах. Workflow `Release` запускается только после успешного `Validate` для push в `main`, повторно проверяет метаданные, затем создаёт тег и GitHub Release.

## Пакетные проверки

Workflow запускается на каждый `push` и `pull_request`, получает полную историю Git и Python 3.12: [`.github/workflows/validate.yml:3-23`](../../../.github/workflows/validate.yml#L3-L23).

| Команда | Проверка и используемые файлы |
|---|---|
| `python3 skills/x9-skill-creator/scripts/test_validate.py` | Регрессионные сценарии основного валидатора: YAML, runtime-профили, ссылки, ресурсы и типы метаданных. Evidence: [`test_validate.py:12-16`](../../../skills/x9-skill-creator/scripts/test_validate.py#L12-L16), [`test_validate.py:37-212`](../../../skills/x9-skill-creator/scripts/test_validate.py#L37-L212). |
| `for skill in skills/*; do python3 .../validate.py --runtime portable --runtime claude --runtime codex "$skill"; done` | Каждый каталог `skills/*`: `SKILL.md`, frontmatter, runtime-совместимость, лимиты полей, мусор, `TODO`, возможные секреты, локальные ссылки, достижимость ресурсов и синтаксис скриптов. Evidence: [`validate.yml:25-31`](../../../.github/workflows/validate.yml#L25-L31), [`validate.py:238-373`](../../../skills/x9-skill-creator/scripts/validate.py#L238-L373), [`validate.py:375-490`](../../../skills/x9-skill-creator/scripts/validate.py#L375-L490). |
| `python3 skills/x9-agent-instructions/scripts/test_check_globals.py` | Извлечение общего блока инструкций и текстовые инварианты двух навыков. Тест использует временные фикстуры, а не опубликованные `global-files/*`. Evidence: [`test_check_globals.py:11-68`](../../../skills/x9-agent-instructions/scripts/test_check_globals.py#L11-L68). |
| `python3 skills/x9-diagrams/scripts/test_check_scene.py` | Структурный валидатор Excalidraw: схема сцены, элементы, связи и шрифты. Evidence: [`test_check_scene.py:117-170`](../../../skills/x9-diagrams/scripts/test_check_scene.py#L117-L170). |
| `python3 skills/x9-okf-docs/scripts/test_okf.py` | Профили и версии OKF, инвентаризация, зарезервированные файлы и безопасное применение изменений. Evidence: [`test_okf.py:54-168`](../../../skills/x9-okf-docs/scripts/test_okf.py#L54-L168). |
| `python3 skills/x9-research/scripts/test_validate_html.py` | Пара Markdown/HTML: язык, якоря, структура, внешние runtime-ресурсы, заглушки и URL источников. Evidence: [`test_validate_html.py:40-148`](../../../skills/x9-research/scripts/test_validate_html.py#L40-L148). |
| `printf '@AGENTS.md\n' \| cmp - CLAUDE.md` | Корневой `CLAUDE.md` должен содержать только импорт `@AGENTS.md` с конечным переводом строки. Evidence: [`validate.yml:40-41`](../../../.github/workflows/validate.yml#L40-L41), [`AGENTS.md:37-40`](../../../AGENTS.md#L37-L40). |
| `python3 scripts/check_package.py` | Оба plugin-манифеста и оба marketplace-манифеста: обязательные поля, SemVer, имена, пути, Codex-интерфейс, PNG-ассеты, policy и category. Evidence: [`check_package.py:52-104`](../../../scripts/check_package.py#L52-L104). |
| `python3 scripts/check_public.py` | Отслеживаемые и неигнорируемые неотслеживаемые файлы: секреты, токены, JWT, персональные пути, e-mail и приватные шаблоны имён. Evidence: [`check_public.py:9-57`](../../../scripts/check_public.py#L9-L57). |
| `python3 scripts/test_prepare_release.py` | Регрессии покрытия changelog, классификации release-relevant путей и учёта обеих сторон перемещения. Evidence: [`test_prepare_release.py:40-91`](../../../scripts/test_prepare_release.py#L40-L91). |
| `python3 scripts/prepare_release.py --check` | Версии, секция текущей версии в `CHANGELOG.md`, `Unreleased`, Git-теги и изменения с текущего или предыдущего тега. Evidence: [`prepare_release.py:152-183`](../../../scripts/prepare_release.py#L152-L183). |
| `gitleaks/gitleaks-action@...` | Полная история Git на секреты. Evidence: [`validate.yml:54-57`](../../../.github/workflows/validate.yml#L54-L57). |

Полный автоматический набор задан в [`.github/workflows/validate.yml:25-57`](../../../.github/workflows/validate.yml#L25-L57).

## Выпуск версии

### Источники версии и метаданных

Текущая версия `2.4.0` записана в [`.claude-plugin/plugin.json:3`](../../../.claude-plugin/plugin.json#L3) и [`.codex-plugin/plugin.json:3`](../../../.codex-plugin/plugin.json#L3). Одинаковый строгий SemVer проверяют [`check_package.py:52-88`](../../../scripts/check_package.py#L52-L88) и [`prepare_release.py:165-173`](../../../scripts/prepare_release.py#L165-L173).

Marketplace-файлы отдельной версии не содержат. Они должны совпадать по имени `xonika9`, имени плагина `x9-agent-skills`, источнику, политике установки и категории: [`check_package.py:91-104`](../../../scripts/check_package.py#L91-L104).

### Подготовка и публикация

1. Тип повышения версии определяется самым сильным изменением с последнего публичного тега: [`CONTRIBUTING.md:25-34`](../../../CONTRIBUTING.md#L25-L34).
2. Владелец должен подтвердить версию: [`.claude/skills/release/SKILL.md:51-60`](../../../.claude/skills/release/SKILL.md#L51-L60).
3. Содержимое `Unreleased` переносится в `## X.Y.Z - YYYY-MM-DD`, остаётся пустой шаблон из четырёх разделов, оба манифеста получают одну версию: [`.claude/skills/release/SKILL.md:62-71`](../../../.claude/skills/release/SKILL.md#L62-L71).
4. Выполняется локальный набор из [`.claude/skills/release/references/checks.md:5-35`](../../../.claude/skills/release/references/checks.md#L5-L35).

`Release` запускается после завершения `Validate`, но job выполняется только для успешного `push` в `main`: [`.github/workflows/release.yml:3-8`](../../../.github/workflows/release.yml#L3-L8), [`.github/workflows/release.yml:20-30`](../../../.github/workflows/release.yml#L20-L30).

Workflow повторно выполняет:

```bash
python3 scripts/check_package.py
python3 scripts/prepare_release.py \
  --notes-out "$RUNNER_TEMP/release-notes.md" \
  --github-output "$GITHUB_OUTPUT"
```

Evidence: [`.github/workflows/release.yml:32-38`](../../../.github/workflows/release.yml#L32-L38). Затем workflow создаёт или проверяет тег `vX.Y.Z` и создаёт GitHub Release: [`.github/workflows/release.yml:40-69`](../../../.github/workflows/release.yml#L40-L69).

### Блокирующие условия

- Любое падение `Validate`: [`release.yml:20-24`](../../../.github/workflows/release.yml#L20-L24).
- Разные или невалидные версии манифестов: [`prepare_release.py:165-171`](../../../scripts/prepare_release.py#L165-L171).
- Нет заголовка текущей версии вида `## X.Y.Z - YYYY-MM-DD`: [`prepare_release.py:131-148`](../../../scripts/prepare_release.py#L131-L148).
- Для новой версии пуст хотя бы один обязательный раздел заметок или не очищен `Unreleased`: [`prepare_release.py:87-97`](../../../scripts/prepare_release.py#L87-L97), [`prepare_release.py:175-183`](../../../scripts/prepare_release.py#L175-L183).
- Для существующего тега есть release-relevant изменения, но `Unreleased` пуст: [`prepare_release.py:21-35`](../../../scripts/prepare_release.py#L21-L35), [`prepare_release.py:75-84`](../../../scripts/prepare_release.py#L75-L84).
- Существующий тег указывает не на проверенный SHA, если GitHub Release ещё отсутствует: [`release.yml:51-57`](../../../.github/workflows/release.yml#L51-L57).
- Любая неуспешная команда документированного локального release gate: [`.claude/skills/release/SKILL.md:75-79`](../../../.claude/skills/release/SKILL.md#L75-L79).

## Противоречия и пробелы

1. `CONTRIBUTING.md` отстаёт от CI: в package-wide списке отсутствуют `test_check_scene.py`, `test_validate_html.py`, `test_prepare_release.py` и Gitleaks. Evidence: [`CONTRIBUTING.md:38-55`](../../../CONTRIBUTING.md#L38-L55) против [`validate.yml:33-57`](../../../.github/workflows/validate.yml#L33-L57).
2. Локальный release gate шире CI, но не покрывает его целиком. Он добавляет `check_global_files.py`, Claude CLI-валидаторы, установочный smoke-test, `git diff --check` и `humanizer-ru`, тогда как Gitleaks есть только в CI. Evidence: [`checks.md:16-35`](../../../.claude/skills/release/references/checks.md#L16-L35), [`validate.yml:54-57`](../../../.github/workflows/validate.yml#L54-L57).
3. CI не сверяет фактическую синхронность опубликованных глобальных инструкций. Такая сверка шести персональных и опубликованных файлов есть только в локальном [`check_global_files.py:7-44`](../../../.claude/skills/release/scripts/check_global_files.py#L7-L44).
4. Правила выбора `MAJOR`, `MINOR` и `PATCH` документированы, но скрипт не сравнивает новую версию численно с предыдущей и не определяет допустимый bump. Evidence: [`prepare_release.py:38-43`](../../../scripts/prepare_release.py#L38-L43), [`prepare_release.py:122-128`](../../../scripts/prepare_release.py#L122-L128) против [`CONTRIBUTING.md:27-32`](../../../CONTRIBUTING.md#L27-L32).
5. При уже существующем GitHub Release workflow выходит до проверки SHA тега. Evidence: [`release.yml:46-57`](../../../.github/workflows/release.yml#L46-L57).
6. Наличие workflow не доказывает, что `Validate` обязателен для слияния PR. Правила защиты `main` находятся в настройках GitHub и в репозитории не представлены. Evidence: [`validate.yml:3-5`](../../../.github/workflows/validate.yml#L3-L5).

## Реестр источников

| Утверждение | Основной источник | Проверка на опровержение | Статус |
|---|---|---|---|
| Состав автоматического барьера | `.github/workflows/validate.yml` | Сопоставлен с `CONTRIBUTING.md` и локальным release checklist | Подтверждено |
| Источники и синхронность версии | Оба `plugin.json`, `check_package.py`, `prepare_release.py` | Marketplace-файлы проверены на отдельное поле версии | Подтверждено |
| Условия автоматической публикации | `.github/workflows/release.yml` | Проверены ранний выход и конфликт SHA тега | Подтверждено с указанным пробелом |
| Полнота локального release gate | `.claude/skills/release/references/checks.md` | Сопоставлен с обоими workflow | Подтверждено с расхождениями |

Независимая перепроверка выводов выявила и уточнила расхождение между локальным gate и CI, ранний выход до проверки SHA и отсутствие в репозитории правил защиты ветки.

## Ограничения

- Настройки branch protection и rulesets GitHub не проверялись.
- Во время исследования внешние Claude CLI-валидаторы и установочный smoke-test не запускались.
- Отчёт описывает текущий рабочий каталог, в котором до исследования уже были незакоммиченные изменения.
