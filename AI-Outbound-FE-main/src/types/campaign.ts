export interface Campaign {
    id?: string;
    campaignName: string;
    description?: string;
    owner_id?: string;
    users?: string[];
    businessName?: string;
    fullname?: string;
    email?: string;
    hasEbook?: boolean;
    ebookPath?: string;
    created_at?: string;
    updated_at?: string;
    campaignDate?: string;
    maxRetry?: number;
    owner_name?: string;
    owner_email?: string;
}

export interface CampaignUser {
    id: string;
    name: string;
    email: string;
    role: string;
}
