import type { Conversation } from '../types/api'

/**
 * Resolve the avatar/name to show for a conversation.
 *
 * Direct chats are labelled with the *other* participant; groups use their
 * title (and initials, since we have no group image).
 */
export function conversationPeer(
  conversation: Conversation,
  currentUserId?: number,
): { name: string; avatar: string } {
  if (conversation.kind === 'direct') {
    const other = conversation.members.find((member) => member.user_id !== currentUserId)
    return {
      name: other?.display_name || other?.username || conversation.display_title,
      avatar: other?.avatar || '',
    }
  }
  return { name: conversation.display_title, avatar: '' }
}
