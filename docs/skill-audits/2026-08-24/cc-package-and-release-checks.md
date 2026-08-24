# Исследование: пакетные проверки и выпуск версии

- Дата: 2026-08-24
- Действие: Research (read-only, изменений в репозитории не вносилось)
- Доказательства: Static — чтение файлов плюс локальный прогон четырёх скриптов только на чтение
- Состояние на момент исследования: версия `2.4.0`, последний тег `v2.4.0`

## 1. Пакетные проверки

Единая точка входа — workflow [validate.yml](../../../.github/workflows/validate.yml) (запускается на `push` и `pull_request`, Python 3.12, `fetch-depth: 0`). Он выполняет шесть групп шагов:

| Шаг | Что проверяет | Evidence |
|---|---|---|
| Валидаторы скиллов | Для каждого каталога `skills/*` — фронтматтер под три рантайма (`portable`, `claude`, `codex`), плюс самотест валидатора | `validate.yml:29-35` |
| Регрессионные тесты скиллов | `x9-agent-instructions`, `x9-diagrams`, `x9-okf-docs`, `x9-research` | `validate.yml:36-39` |
| Импорт инструкций | Корневой `CLAUDE.md` должен быть ровно `@AGENTS.md` + перевод строки (`printf … \| cmp - CLAUDE.md`) | `validate.yml:41-42` |
| Метаданные пакета | `scripts/check_package.py` | `validate.yml:44-45` |
| Публичность данных | `scripts/check_public.py` | `validate.yml:47-48` |
| Релизные метаданные | `scripts/test_prepare_release.py` и `scripts/prepare_release.py --check` | `validate.yml:50-53` |
| История Git | Gitleaks (закреплённый SHA) | `validate.yml:55-59` |

Что делает каждый скрипт:

- [check_package.py](../../../scripts/check_package.py) — читает четыре файла: `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`. Требует обязательные строковые поля манифеста, имя ровно `x9-agent-skills`, строгий semver, `skills == "./skills/"`, наличие `author.name` (`check_package.py:53-62`); для Codex — блок `interface` с непустыми полями, `brandColor` формата `#RRGGBB`, 1–3 промпта до 128 символов и три PNG-ассета, существующих и не выходящих за корень (`check_package.py:65-81`, проверка пути — `check_package.py:41-52`). Затем сверяет равенство версий Claude/Codex, наличие `skills/`, имя marketplace `xonika9`, ровно один плагин в каждом marketplace, `source == "./"` у Claude, `source`/`policy` у Codex и совпадение `category` в Codex-marketplace с `interface.category` (`check_package.py:90-107`).
- [check_public.py](../../../scripts/check_public.py) — обходит `git ls-files --cached --others --exclude-standard` и ищет по regex приватные ключи, AWS/GitHub-токены, API-ключи, JWT, персональные пути домашних каталогов macOS и Linux, паттерн приватных проектов `agent-for-*` и e-mail (исключение — адреса `@users.noreply.github.com`) (`check_public.py:11-34`, исключение — `check_public.py:56-59`).
- [validate.py](../../../skills/x9-skill-creator/scripts/validate.py) — по каждому скиллу: разбор YAML-фронтматтера, допустимые и обязательные ключи по рантайму, hyphen-case имени и совпадение с именем папки, лимиты длины `name`/`description`, запрет угловых скобок в описании для Codex, типы `metadata`/`hooks`/`allowed-tools`, непустое тело, запрет мусорных файлов и оставшихся плейсхолдеров, поиск встроенных секретов, пустые каталоги ресурсов, битые и выходящие за корень локальные ссылки (`validate.py:238-400`).
- [test_prepare_release.py](../../../scripts/test_prepare_release.py) — не трогает реальный `CHANGELOG.md`, а прогоняет функции `has_unreleased_entries`, `is_release_relevant`, `validate_development_changelog` на синтетических текстах и проверяет во временном git-репозитории, что `changed_paths_since` видит обе стороны `git mv` и untracked-файлы (`test_prepare_release.py:40-88`).

Фактический прогон на момент исследования: `check_package.py`, `check_public.py`, `test_prepare_release.py`, `prepare_release.py --check` — все четыре вернули `PASS` (последний: `PASS: release metadata for v2.4.0`).

Вне CI существуют ещё две проверки: `claude plugin validate …` и `npx skills add . --list` (`CONTRIBUTING.md:52-54`), а также `check_global_files.py` — он сверяет побайтово блок между маркерами `BEGIN/END SHARED PERSONAL CORE` в шести файлах: трёх установленных личных глобальных файлах OpenCode, Claude Code и Codex и трёх репозиторных под `global-files/<harness>/` (`.claude/skills/release/scripts/check_global_files.py:8-21`).

## 2. Выпуск версии

**Где хранится версия.** Единственные источники — `version` в [.claude-plugin/plugin.json](../../../.claude-plugin/plugin.json) и [.codex-plugin/plugin.json](../../../.codex-plugin/plugin.json) (на момент исследования обе `2.4.0`). Тег вычисляется как `v{version}` (`prepare_release.py:173`), нигде отдельно не хранится; последний тег в репозитории — `v2.4.0`.

**Что обязано совпадать.**

- Версии обоих манифестов между собой — проверяется дважды: `check_package.py:93` и `prepare_release.py:167-171`.
- Имя плагина `x9-agent-skills` и имя marketplace `xonika9` во всех четырёх файлах метаданных (см. выше), как и требует `AGENTS.md:28`.
- В `CHANGELOG.md` должен существовать заголовок ровно `## X.Y.Z - YYYY-MM-DD` с непустым телом, иначе `SystemExit` (`prepare_release.py:135-150`).
- Секции `Unreleased`: `Highlights`, `Install / update`, `Compatibility`, `Breaking changes` (`prepare_release.py:16-21`).

**Что блокирует релиз.** `prepare_release.py` ведёт себя по-разному в зависимости от того, существует ли тег текущей версии (`prepare_release.py:175-178`):

- тег есть (обычная разработка) → `validate_development_changelog`: если изменились «релизно значимые» файлы, а `Unreleased` пуст — падение. Значимыми считаются префиксы `skills/`, `global-files/`, `assets/`, `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/` и файлы `README.md`, `README.ru.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` (`prepare_release.py:21-37`); список изменений берётся как diff от тега плюс untracked (`prepare_release.py:117-130`).
- тега нет (кандидат на релиз) → `validate_new_release`: все четыре секции нового раздела должны быть непустыми, а `Unreleased` — полностью пустым (`prepare_release.py:87-98`); дополнительно печатается `AUDIT` со списком всех файлов, изменившихся с предыдущего тега (`prepare_release.py:179-183`).

**Публикация.** [release.yml](../../../.github/workflows/release.yml) не запускается вручную: он висит на `workflow_run` от Validate и срабатывает только при `conclusion == success`, `event == push`, `head_branch == main` (`release.yml:20-24`). Далее чекаутит именно провалидированный SHA, повторно гоняет `check_package.py` и `prepare_release.py` уже с записью нот и `version`/`tag` в `GITHUB_OUTPUT` (`release.yml:34-41`), и затем: если релиз уже есть — выходит; если тег есть, но указывает на другой коммит — падает с ошибкой; иначе создаёт аннотированный тег от `RELEASE_SHA`, пушит его и создаёт GitHub Release с `--verify-tag` и нотами из changelog (`release.yml:43-69`).

Процедурная часть (выбор бампа, подтверждение версии через структурированный вопрос, перенос `Unreleased` в датированный раздел, синхронизация README и `global-files/`) описана в приватном скилле `.claude/skills/release/SKILL.md`; ручное создание тега там прямо запрещено — тегом владеет workflow.

## 3. Расхождения и асимметрии

1. **Список проверок в CONTRIBUTING неполон относительно CI.** `CONTRIBUTING.md:41-55` не содержит `skills/x9-diagrams/scripts/test_check_scene.py`, `skills/x9-research/scripts/test_validate_html.py` и `scripts/test_prepare_release.py`, которые CI выполняет (`validate.yml:36-51`) и которые перечислены в релизном `.claude/skills/release/references/checks.md:13-19`. Контрибьютор, следующий CONTRIBUTING, получит красный CI.
2. **`claude plugin validate` и `npx skills add . --list` требуются документацией, но не воспроизводятся в CI.** `AGENTS.md:29` и `CONTRIBUTING.md:52-54` предписывают их запуск, в `validate.yml` их нет. Формально противоречия нет (AGENTS.md сам называет `check_package.py` воспроизводимым гейтом), но de facto эти проверки — только локальные и никем не принуждаются.
3. **`check_global_files.py` — обязательный релизный гейт, невоспроизводимый в CI и у контрибьюторов.** Он входит в `checks.md:16` и в раздел синхронизации SKILL.md, но читает три файла из домашнего каталога мейнтейнера (`check_global_files.py:12-15`). При этом `global-files/` считается релизно значимым префиксом (`prepare_release.py:23`) — то есть содержимое, влияющее на релиз, проверяется только на одной машине.
4. **Формулировка в AGENTS.md описывает лишь половину поведения `--check`.** `AGENTS.md:35` говорит только про блокировку при пустом `Unreleased`. Но в ветке «тега ещё нет» тот же самый флаг требует ровно обратного — `Unreleased` должен быть пустым, иначе падение (`prepare_release.py:91-98`). Из документации это не следует.
5. **Асимметрия `category` между marketplace-файлами.** В `.claude-plugin/marketplace.json` — `"productivity"` (строчными), в `.agents/plugins/marketplace.json` и Codex-интерфейсе — `"Productivity"`. `check_package.py` сверяет только пару Codex↔Codex (`check_package.py:107`), Claude-категория не проверяется вообще. Гейт это не ломает, но дрейф значения на стороне Claude пройдёт незамеченным.
6. **Скрипты и workflow не покрыты требованием changelog.** Тест явно фиксирует `assert not prepare_release.is_release_relevant("scripts/check_public.py")` (`test_prepare_release.py:78`), тогда как `AGENTS.md:33` требует обновлять `CHANGELOG.md` при каждом user-visible изменении. Изменение гейтов, CI или самого релизного процесса пользовательски видимо, но автоматикой не отслеживается.
7. **Приватный скилл `release` не проходит валидатор скиллов.** Цикл в CI и в `checks.md` идёт по `skills/*`, а канонический источник лежит в `.claude/skills/release` (через симлинк `.agents/skills → ../.claude/skills`), поэтому его фронтматтер и ссылки не валидируются ничем.
