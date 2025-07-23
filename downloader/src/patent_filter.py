import re

pattern = r'\b(IC50|IC[\s_\-]*50|IC₅₀|ic50|ic[\s_\-]*50|Ki|ki|K[iI]|k[iI]|Kd|kd|K[dD]|k[dD]|EC50|EC[\s_\-]*50|EC₅₀|ec50|ec[\s_\-]*50|pIC50|pIC[\s_\-]*50|pIC₅₀|pic50|pic[\s_\-]*50|pEC50|pEC[\s_\-]*50|pEC₅₀|pec50|pec[\s_\-]*50|pKi|pki|pK[iI]|pk[iI]|pKd|pkd|pK[dD]|pk[dD]|logIC50|log[\s]*IC50|log[\s]*\([\s]*IC50[\s]*\)|-log[\s]*\([\s]*IC50[\s]*\)|logKi|log[\s]*Ki|log[\s]*\([\s]*Ki[\s]*\)|-log[\s]*\([\s]*Ki[\s]*\)|logKd|log[\s]*Kd|log[\s]*\([\s]*Kd[\s]*\)|-log[\s]*\([\s]*Kd[\s]*\)|logEC50|log[\s]*EC50|log[\s]*\([\s]*EC50[\s]*\)|-log[\s]*\([\s]*EC50[\s]*\)|inhibition[\s\-]*constant|dissociation[\s\-]*constant|binding[\s\-]*constant|half[\s\-]*maximal[\s\-]*inhibitory[\s\-]*concentration|half[\s\-]*maximal[\s\-]*effective[\s\-]*concentration|binding[\s\-]*assay)\b'
def patent_filter(patent: dict) -> bool:
    if 'content' in patent:
        if re.search(pattern, patent['content'], re.IGNORECASE):
            return True
    return False