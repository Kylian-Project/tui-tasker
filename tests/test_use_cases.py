import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from todo.application.use_cases import (
    create_task,
    delete_task,
    update_task,
    change_task_status,
)
from todo.domain.task import Task, TaskStatus


# =========================
# Mocks
# =========================

@pytest.fixture
def mock_repository():
    """Mock du Repository"""
    return Mock()


@pytest.fixture
def mock_notifier():
    """Mock du Notifier"""
    return Mock()


# =========================
# Tests create_task
# =========================

def test_create_task_success(mock_repository, mock_notifier):
    """Test création d'une tâche valide"""

    task = create_task(
        repository=mock_repository,
        notifier=mock_notifier,
        title="Ma tâche",
        description="Description test",
    )

    assert task.title == "Ma tâche"
    assert task.description == "Description test"
    assert task.status == TaskStatus.IN_PROGRESS
    mock_repository.add.assert_called_once()
    mock_notifier.notify.assert_called_once()


def test_create_task_with_due_date(mock_repository, mock_notifier):
    """Test création d'une tâche avec date d'échéance"""
    due = date.today() + timedelta(days=7)
    
    task = create_task(
        repository=mock_repository,
        notifier=mock_notifier,
        title="Tâche avec deadline",
        due_date=due,
    )

    assert task.due_date == due


def test_create_task_title_empty(mock_repository, mock_notifier):
    """Test : titre vide doit lever une ValueError"""
    with pytest.raises(ValueError, match="Title is required"):
        create_task(
            repository=mock_repository,
            notifier=mock_notifier,
            title="",
        )


def test_create_task_title_too_long(mock_repository, mock_notifier):
    """Test : titre > 30 caractères doit lever une ValueError"""
    with pytest.raises(ValueError, match="1-30 characters"):
        create_task(
            repository=mock_repository,
            notifier=mock_notifier,
            title="A" * 31,  # 31 caractères
        )


def test_create_task_description_too_long(mock_repository, mock_notifier):
    """Test : description > 115 caractères doit lever une ValueError"""
    with pytest.raises(ValueError, match="must not exceed 115"):
        create_task(
            repository=mock_repository,
            notifier=mock_notifier,
            title="Test",
            description="A" * 116,  # 116 caractères
        )


# =========================
# Tests delete_task
# =========================

def test_delete_task_success(mock_repository, mock_notifier):
    """Test suppression d'une tâche existante"""

    existing_task = Task(id=1, title="Tâche à supprimer")
    mock_repository.get.return_value = existing_task

    result = delete_task(mock_repository, mock_notifier, task_id=1)

    assert result is True
    mock_repository.get.assert_called_once_with(1)
    mock_repository.delete.assert_called_once_with(1)
    mock_notifier.notify.assert_called_once()


def test_delete_task_not_found(mock_repository, mock_notifier):
    """Test suppression d'une tâche inexistante"""
    mock_repository.get.return_value = None

    result = delete_task(mock_repository, mock_notifier, task_id=999)

    assert result is False
    mock_repository.delete.assert_not_called()
    mock_notifier.notify.assert_not_called()


# =========================
# Tests update_task
# =========================

def test_update_task_title(mock_repository, mock_notifier):
    """Test modification du titre d'une tâche"""
    existing_task = Task(id=1, title="Ancien titre")
    mock_repository.get.return_value = existing_task
    mock_repository.update.return_value = existing_task

    updated = update_task(
        repository=mock_repository,
        notifier=mock_notifier,
        task_id=1,
        title="Nouveau titre",
    )

    assert updated.title == "Nouveau titre"
    mock_repository.update.assert_called_once()
    mock_notifier.notify.assert_called_once()


def test_update_task_not_found(mock_repository, mock_notifier):
    """Test modification d'une tâche inexistante"""
    mock_repository.get.return_value = None

    result = update_task(
        repository=mock_repository,
        notifier=mock_notifier,
        task_id=999,
        title="Test",
    )

    assert result is None
    mock_repository.update.assert_not_called()


def test_update_task_title_too_long(mock_repository, mock_notifier):
    """Test : titre > 30 caractères"""
    existing_task = Task(id=1, title="Test")
    mock_repository.get.return_value = existing_task

    with pytest.raises(ValueError, match="1-30 characters"):
        update_task(
            repository=mock_repository,
            notifier=mock_notifier,
            task_id=1,
            title="A" * 31,
        )


# =========================
# Tests change_task_status
# =========================

def test_change_task_status_to_done(mock_repository, mock_notifier):
    """Test changement de statut vers DONE"""
    task = Task(id=1, title="Test", status=TaskStatus.IN_PROGRESS)
    mock_repository.get.return_value = task
    mock_repository.update.return_value = task

    updated = change_task_status(
        repository=mock_repository,
        notifier=mock_notifier,
        task_id=1,
        new_status=TaskStatus.DONE,
    )

    assert updated.status == TaskStatus.DONE
    mock_repository.update.assert_called_once()
    mock_notifier.notify.assert_called_once()


def test_change_task_status_to_in_progress(mock_repository, mock_notifier):
    """Test changement de statut vers IN_PROGRESS"""
    task = Task(id=1, title="Test", status=TaskStatus.DONE)
    mock_repository.get.return_value = task
    mock_repository.update.return_value = task

    updated = change_task_status(
        repository=mock_repository,
        notifier=mock_notifier,
        task_id=1,
        new_status=TaskStatus.IN_PROGRESS,
    )

    assert updated.status == TaskStatus.IN_PROGRESS


def test_change_task_status_not_found(mock_repository, mock_notifier):
    """Test changement de statut d'une tâche inexistante"""
    mock_repository.get.return_value = None

    result = change_task_status(
        repository=mock_repository,
        notifier=mock_notifier,
        task_id=999,
        new_status=TaskStatus.DONE,
    )

    assert result is None
    mock_notifier.notify.assert_not_called()


def test_change_task_status_overdue(mock_repository, mock_notifier):
    """Test qu'une tâche en retard reste OVERDUE même si on change le statut"""
    yesterday = date.today() - timedelta(days=1)
    task = Task(id=1, title="Test", status=TaskStatus.IN_PROGRESS, due_date=yesterday)
    mock_repository.get.return_value = task
    mock_repository.update.return_value = task

    updated = change_task_status(
        repository=mock_repository,
        notifier=mock_notifier,
        task_id=1,
        new_status=TaskStatus.IN_PROGRESS,
    )

    # La teche doit etre OVERDUE automatiquement
    assert updated.status == TaskStatus.OVERDUE
