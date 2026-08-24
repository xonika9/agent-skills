# Проверки пакета и выпуск версии

- Объект: репозиторий `agent-skills`
- Дата проверки: 2026-08-24
- Доказательства: файлы репозитория, локальные команды и история Git
- Режим исследования: без изменения файлов проекта

## Краткий итог

В репозитории работают два последовательных контура. Workflow `Validate` проверяет каждый `push` и pull request. Workflow `Release` ждёт успешного `Validate` для push в `main`, повторно сверяет метаданные, создаёт тег на проверенном коммите и публикует GitHub Release. Источники: [`validate.yml`](../../../.github/workflows/validate.yml#L3-L23), [`release.yml`](../../../.github/workflows/release.yml#L3-L30).

Версия хранится в двух манифестах. На момент проверки оба содержали `2.4.0`: [Claude manifest](../../../.claude-plugin/plugin.json#L1-L4), [Codex manifest](../../../.codex-plugin/plugin.json#L1-L4). Скрипты требуют строгий SemVer и равенство этих двух значений: [`check_package.py`](../../../scripts/check_package.py#L52-L57), [`prepare_release.py`](../../../scripts/prepare_release.py#L165-L173).

## 1. Пакетные проверки

### Что запускает CI

`Validate` получает полную историю Git и настраивает Python 3.12. Это нужно проверке changelog относительно тегов и сканированию истории: [`validate.yml`](../../../.github/workflows/validate.yml#L15-L23).

| Команда или шаг | Что проверяет | Какие файлы использует | Evidence |
|---|---|---|---|
| `python3 skills/x9-skill-creator/scripts/test_validate.py` | Регрессии основного валидатора: YAML, дубли ключей, профили сред исполнения, ссылки и достижимость ресурсов. | Временные тестовые пакеты и `validate.py`. | [`test_validate.py`](../../../skills/x9-skill-creator/scripts/test_validate.py#L12-L24), [начало сценариев](../../../skills/x9-skill-creator/scripts/test_validate.py#L37-L65) |
| `for skill in skills/*; do python3 .../validate.py --runtime portable --runtime claude --runtime codex "$skill"; done` | Каждый каталог в `skills/`: `SKILL.md`, frontmatter трёх профилей, локальные ссылки, недостижимые ресурсы, заглушки, возможные секреты, синтаксис Python и Shell. | Все файлы соответствующего скилла. | [запуск CI](../../../.github/workflows/validate.yml#L25-L31), [frontmatter](../../../skills/x9-skill-creator/scripts/validate.py#L238-L327), [ресурсы и ссылки](../../../skills/x9-skill-creator/scripts/validate.py#L358-L470), [проверка синтаксиса](../../../skills/x9-skill-creator/scripts/validate.py#L472-L490) |
| `python3 skills/x9-agent-instructions/scripts/test_check_globals.py` | Точное извлечение общего блока инструкций и текстовые контракты двух скиллов. | `x9-agent-instructions/SKILL.md`, `x9-context-files-generator/SKILL.md`, временные файлы. | [`test_check_globals.py`](../../../skills/x9-agent-instructions/scripts/test_check_globals.py#L11-L16), [контрактные тесты](../../../skills/x9-agent-instructions/scripts/test_check_globals.py#L36-L68) |
| `python3 skills/x9-diagrams/scripts/test_check_scene.py` | Структурные регрессии валидатора Excalidraw: элементы, связи, текст, размеры и нормализация. | `check_scene.py` и тестовые сцены в памяти или временных файлах. | [`test_check_scene.py`](../../../skills/x9-diagrams/scripts/test_check_scene.py#L1-L16) |
| `python3 skills/x9-okf-docs/scripts/test_okf.py` | Совместимость OKF v0.2/v0.1, профили проверки, reserved-файлы, инвентаризацию и обновление frontmatter. | `insert_frontmatter.py`, `validate_okf.py`, временные Markdown-наборы и Git-репозитории. | [`test_okf.py`](../../../skills/x9-okf-docs/scripts/test_okf.py#L14-L24), [начало сценариев](../../../skills/x9-okf-docs/scripts/test_okf.py#L54-L84) |
| `python3 skills/x9-research/scripts/test_validate_html.py` | Соответствие пары Markdown/HTML: язык, источники, якоря, автономность HTML, отсутствие заглушек и служебных цитат. | `validate_html.py`, временные `report.md` и `report.html`. | [`test_validate_html.py`](../../../skills/x9-research/scripts/test_validate_html.py#L10-L16), [сценарии](../../../skills/x9-research/scripts/test_validate_html.py#L40-L111) |
| `printf '@AGENTS.md\n' \| cmp - CLAUDE.md` | Корневой `CLAUDE.md` должен содержать ровно `@AGENTS.md` с финальным переводом строки. | `CLAUDE.md`. | [`validate.yml`](../../../.github/workflows/validate.yml#L40-L41), [`CLAUDE.md`](../../../CLAUDE.md#L1) |
| `python3 scripts/check_package.py` | Манифесты Claude и Codex, имена маркетплейсов, SemVer, пути ресурсов, интерфейс Codex и marketplace policy. | Четыре JSON-файла пакета и каталог `assets/`. | [`check_package.py`](../../../scripts/check_package.py#L78-L106) |
| `python3 scripts/check_public.py` | Приватные ключи, токены, персональные пути, email и приватные шаблоны имён. | Отслеживаемые и неотслеживаемые файлы из `git ls-files`. | [шаблоны](../../../scripts/check_public.py#L9-L29), [перечень файлов](../../../scripts/check_public.py#L32-L57) |
| `python3 scripts/test_prepare_release.py` | Регрессии проверки changelog: пустой `Unreleased`, релизно значимые пути, обе стороны переименования. | `prepare_release.py` и временный Git-репозиторий. | [`test_prepare_release.py`](../../../scripts/test_prepare_release.py#L40-L71), [утверждения](../../../scripts/test_prepare_release.py#L74-L91) |
| `python3 scripts/prepare_release.py --check` | Согласованность версии и состояние `CHANGELOG.md` относительно текущего тега. | Оба plugin manifest, `CHANGELOG.md`, теги, diff и неотслеживаемые файлы. | [`prepare_release.py`](../../../scripts/prepare_release.py#L152-L192) |
| `gitleaks/gitleaks-action` | Секреты в истории Git. | Полная история, полученная checkout. | [`validate.yml`](../../../.github/workflows/validate.yml#L54-L57) |

### Контракт `check_package.py`

Скрипт читает четыре файла: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json` и `.agents/plugins/marketplace.json`. Evidence: [`check_package.py`](../../../scripts/check_package.py#L78-L82).

Оба plugin manifest должны содержать непустые `name`, `version`, `description`, `homepage`, `repository`, `license`, `skills` и объект `author`. Имя фиксировано как `x9-agent-skills`, версия должна соответствовать строгому `X.Y.Z`, путь скиллов фиксирован как `./skills/`. Evidence: [`check_package.py`](../../../scripts/check_package.py#L52-L60).

Codex manifest дополнительно обязан содержать интерфейс, цвет вида `#RRGGBB`, 1-3 стартовых запроса и три PNG-ресурса. Пути ресурсов должны начинаться с `./`, оставаться внутри корня пакета и указывать на существующие файлы. Evidence: [интерфейс](../../../scripts/check_package.py#L62-L75), [разрешение путей](../../../scripts/check_package.py#L38-L49).

Оба маркетплейса называются `xonika9` и содержат ровно один `x9-agent-skills`. Для Codex также фиксированы локальный источник, политика установки и совпадение категории с Codex manifest. Evidence: [`check_package.py`](../../../scripts/check_package.py#L91-L104).

## 2. Выпуск новой версии

### Подготовка кандидата

Репозиторный release-навык предписывает исследовать полный кандидат от последнего публичного `v*`-тега: историю, рабочее дерево, неотслеживаемые файлы, оба README, changelog, манифесты и workflow. Evidence: [`release/SKILL.md`](../../../.claude/skills/release/SKILL.md#L21-L33).

Версию выбирают по самому сильному изменению в полном кандидате. После `1.0.0` несовместимый контракт требует `MAJOR`, обратимо совместимая возможность требует `MINOR`, исправление требует `PATCH`. Выбор подтверждает мейнтейнер через структурированный вопрос. Evidence: [правила SemVer](../../../.claude/skills/release/SKILL.md#L51-L60), [контракт подтверждения](../../../.claude/skills/release/references/version-confirmation.md#L1-L10).

После подтверждения содержимое `Unreleased` переносят в `## X.Y.Z - YYYY-MM-DD`. Вверху оставляют новый пустой шаблон с `Highlights`, `Install / update`, `Compatibility`, `Breaking changes`; оба manifest получают одинаковую версию. Evidence: [`release/SKILL.md`](../../../.claude/skills/release/SKILL.md#L62-L73).

### Что блокирует релиз

До появления нового тега `prepare_release.py` требует:

- строгий SemVer и равенство версий двух манифестов;
- секцию `## X.Y.Z - YYYY-MM-DD` в `CHANGELOG.md`;
- непустые `Highlights`, `Install / update`, `Compatibility`, `Breaking changes` в секции выпуска;
- пустые соответствующие разделы в `Unreleased`.

Evidence: [загрузка и сравнение версий](../../../scripts/prepare_release.py#L38-L43), [поиск заметок](../../../scripts/prepare_release.py#L131-L149), [проверка четырёх разделов](../../../scripts/prepare_release.py#L87-L98), [основная ветка](../../../scripts/prepare_release.py#L165-L183).

Если тег текущей версии уже существует, релизно значимые изменения требуют хотя бы одной записи в `Unreleased`. В перечень входят `skills/`, `global-files/`, `assets/`, plugin и marketplace metadata, оба README и основные публичные документы. Evidence: [перечень путей](../../../scripts/prepare_release.py#L21-L35), [проверка покрытия](../../../scripts/prepare_release.py#L71-L84).

Полный локальный барьер шире CI. Release-навык требует также `check_global_files.py`, оба Claude-валидатора, `npx skills add . --list`, `git diff --check` и сканер `humanizer-ru`. Evidence: [`checks.md`](../../../.claude/skills/release/references/checks.md#L1-L37).

### Автоматическая публикация

Workflow `Release` стартует после завершения `Validate`, но публикует только успешный `push` в `main`. Он получает именно проверенный `head_sha`. Evidence: [триггер](../../../.github/workflows/release.yml#L3-L8), [условие](../../../.github/workflows/release.yml#L18-L24), [checkout](../../../.github/workflows/release.yml#L26-L30).

Перед публикацией workflow повторно выполняет:

```bash
python3 scripts/check_package.py
python3 scripts/prepare_release.py \
  --notes-out "$RUNNER_TEMP/release-notes.md" \
  --github-output "$GITHUB_OUTPUT"
```

Evidence: [`release.yml`](../../../.github/workflows/release.yml#L32-L38).

Тег вычисляется как `v{version}`. Если GitHub Release уже существует, workflow ничего не меняет. Если тег существует на другом SHA, публикация завершается ошибкой; тег не перемещается. Иначе workflow создаёт аннотированный тег на проверенном SHA и GitHub Release с заметками из changelog. Evidence: [вычисление тега](../../../scripts/prepare_release.py#L173-L190), [проверка и создание](../../../.github/workflows/release.yml#L40-L69).

## Расхождения и пробелы

### 1. `CONTRIBUTING.md` и CI перечисляют разные команды

В `CONTRIBUTING.md` нет `test_prepare_release.py`, `test_check_scene.py` и `test_validate_html.py`, хотя CI их запускает. В обратную сторону: документация требует два `claude plugin validate`, `npx skills add . --list` и `git diff --check`, которых в CI нет. Evidence: [локальный список](../../../CONTRIBUTING.md#L36-L58), [CI-регрессии](../../../.github/workflows/validate.yml#L33-L38), [CI-проверки выпуска](../../../.github/workflows/validate.yml#L43-L52).

### 2. Локальный release-gate шире автоматического

Release-навык называет свой набор полным и обязательным, но workflow `Validate` не запускает `check_global_files.py`, Claude-валидаторы, `npx skills`, `git diff --check` и `humanizer-ru`. Это разрыв между объявленным процессом подготовки и автоматически доказуемым барьером. Evidence: [локальный gate](../../../.claude/skills/release/references/checks.md#L1-L37), [автоматический gate](../../../.github/workflows/validate.yml#L25-L57).

### 3. Сообщение `metadata agree` шире фактической проверки

Между Claude и Codex manifest напрямую сравнивается только `version`. `description`, `homepage`, `repository`, `license` и `author` проверяются на наличие в каждом файле, но не на равенство. При этом успешный вывод сообщает, что метаданные согласованы. Сейчас значения совпадают, однако будущая смысловая рассинхронизация этих полей не остановит скрипт. Evidence: [индивидуальная проверка](../../../scripts/check_package.py#L52-L60), [сравнение версии](../../../scripts/check_package.py#L84-L89), [итоговое сообщение](../../../scripts/check_package.py#L106).

### 4. Сверка release notes остаётся ручной

Для новой версии `prepare_release.py` печатает `AUDIT` со списком изменённых файлов, но не проверяет, описан ли смысл каждого изменения. Семантическую сверку требует release-навык. Evidence: [печать списка](../../../scripts/prepare_release.py#L179-L183), [ручная сверка](../../../.claude/skills/release/SKILL.md#L31-L39).

## Фактическая проверка

Во время исследования без изменения файлов прошли:

```text
python3 skills/x9-skill-creator/scripts/test_validate.py
for skill in skills/*; do
  python3 skills/x9-skill-creator/scripts/validate.py \
    --runtime portable --runtime claude --runtime codex "$skill"
done
python3 skills/x9-agent-instructions/scripts/test_check_globals.py
python3 skills/x9-diagrams/scripts/test_check_scene.py
python3 skills/x9-okf-docs/scripts/test_okf.py
python3 skills/x9-research/scripts/test_validate_html.py
printf '@AGENTS.md\n' | cmp - CLAUDE.md
python3 scripts/check_package.py
python3 scripts/check_public.py
python3 scripts/test_prepare_release.py
python3 scripts/prepare_release.py --check
claude plugin validate .claude-plugin/marketplace.json
claude plugin validate .claude-plugin/plugin.json
```

Все команды завершились успешно. Валидатор Claude выдал одно неблокирующее предупреждение: корневой `CLAUDE.md` не загружается как контекст плагина.

Локальный `gitleaks` не запускался: исполняемого файла в среде нет, а репозиторий подключает его как GitHub Action. Также не запускались дополнительные команды полного release-gate: `check_global_files.py`, `npx skills add . --list`, `git diff --check` и `humanizer-ru`; они не входили в исходное исследование.

На момент исследования тег `v2.4.0` существовал, а `Unreleased` был заполнен. Это нормальное состояние разработки после `2.4.0`, не подготовленный новый выпуск: [`CHANGELOG.md`](../../../CHANGELOG.md#L3-L28).
