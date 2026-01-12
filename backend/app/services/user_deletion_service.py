from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, delete
from app.models.user import User
from app.models.team import TeamNode, TeamEra
from app.models.sponsor import SponsorMaster, SponsorBrand
from app.models.lineage import LineageEvent
from app.models.edit import EditHistory

class UserDeletionService:
    SYSTEM_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
    
    @staticmethod
    async def delete_user_account(
        session: AsyncSession,
        user_id: UUID,
        requesting_user: User
    ) -> None:
        """
        GDPR-compliant account deletion.
        
        1. Validates user can delete (self-deletion only)
        2. Prevents system user deletion
        3. Anonymizes all user references across entities
        4. Hard deletes user record
        """
        # Validation
        if user_id == UserDeletionService.SYSTEM_USER_ID:
            raise ValueError("Cannot delete system user")
        
        # Ensure requesting user is the target user
        # Note: In future if admins can delete users, we'd check role here too.
        if requesting_user.user_id != user_id:
            raise PermissionError("Can only delete own account")
        
        # Anonymize TeamNode
        await session.execute(
            update(TeamNode)
            .where(TeamNode.created_by == user_id)
            .values(created_by=None)
        )
        await session.execute(
            update(TeamNode)
            .where(TeamNode.last_modified_by == user_id)
            .values(last_modified_by=None)
        )
        
        # Anonymize TeamEra
        await session.execute(
            update(TeamEra)
            .where(TeamEra.created_by == user_id)
            .values(created_by=None)
        )
        await session.execute(
            update(TeamEra)
            .where(TeamEra.last_modified_by == user_id)
            .values(last_modified_by=None)
        )
        
        # Anonymize SponsorMaster
        await session.execute(
            update(SponsorMaster)
            .where(SponsorMaster.created_by == user_id)
            .values(created_by=None)
        )
        await session.execute(
            update(SponsorMaster)
            .where(SponsorMaster.last_modified_by == user_id)
            .values(last_modified_by=None)
        )
        
        # Anonymize SponsorBrand
        await session.execute(
            update(SponsorBrand)
            .where(SponsorBrand.created_by == user_id)
            .values(created_by=None)
        )
        await session.execute(
            update(SponsorBrand)
            .where(SponsorBrand.last_modified_by == user_id)
            .values(last_modified_by=None)
        )
        
        from app.models.sponsor import TeamSponsorLink
        # Anonymize TeamSponsorLink
        await session.execute(
            update(TeamSponsorLink)
            .where(TeamSponsorLink.created_by == user_id)
            .values(created_by=None)
        )
        await session.execute(
            update(TeamSponsorLink)
            .where(TeamSponsorLink.last_modified_by == user_id)
            .values(last_modified_by=None)
        )
        
        # Anonymize LineageEvent
        await session.execute(
            update(LineageEvent)
            .where(LineageEvent.created_by == user_id)
            .values(created_by=None)
        )
        await session.execute(
            update(LineageEvent)
            .where(LineageEvent.last_modified_by == user_id)
            .values(last_modified_by=None)
        )
        
        # Anonymize EditHistory
        await session.execute(
            update(EditHistory)
            .where(EditHistory.user_id == user_id)
            .values(user_id=None)
        )
        await session.execute(
            update(EditHistory)
            .where(EditHistory.reviewed_by == user_id)
            .values(reviewed_by=None)
        )
        
        # Delete user
        await session.execute(
            delete(User).where(User.user_id == user_id)
        )
        
        await session.commit()
