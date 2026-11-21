"""新旧分类的显式名称映射；不修改历史模型响应或原始人工稿。"""
MERGED_AD_SUBTYPE = 'Product embedding / Native advertising'
FORMER_AD_SUBTYPES = frozenset({'Product embedding', 'Native advertising'})
TAXONOMY_VERSION = 'interface_merged_ads_20261103'

def canonical_subtype(parent, subtype):
    if parent == 'Disguised Ad' and subtype in FORMER_AD_SUBTYPES:
        return MERGED_AD_SUBTYPE
    return subtype
