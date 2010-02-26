errors = {}
class KADM5_FAILURE(Exception):
    def __str__(self): return 'KADM5_FAILURE'
errors['43787520'] = KADM5_FAILURE
class KADM5_AUTH_GET(Exception):
    def __str__(self): return 'KADM5_AUTH_GET'
errors['43787521'] = KADM5_AUTH_GET
class KADM5_AUTH_ADD(Exception):
    def __str__(self): return 'KADM5_AUTH_ADD'
errors['43787522'] = KADM5_AUTH_ADD
class KADM5_AUTH_MODIFY(Exception):
    def __str__(self): return 'KADM5_AUTH_MODIFY'
errors['43787523'] = KADM5_AUTH_MODIFY
class KADM5_AUTH_DELETE(Exception):
    def __str__(self): return 'KADM5_AUTH_DELETE'
errors['43787524'] = KADM5_AUTH_DELETE
class KADM5_AUTH_INSUFFICIENT(Exception):
    def __str__(self): return 'KADM5_AUTH_INSUFFICIENT'
errors['43787525'] = KADM5_AUTH_INSUFFICIENT
class KADM5_BAD_DB(Exception):
    def __str__(self): return 'KADM5_BAD_DB'
errors['43787526'] = KADM5_BAD_DB
class KADM5_DUP(Exception):
    def __str__(self): return 'KADM5_DUP'
errors['43787527'] = KADM5_DUP
class KADM5_RPC_ERROR(Exception):
    def __str__(self): return 'KADM5_RPC_ERROR'
errors['43787528'] = KADM5_RPC_ERROR
class KADM5_NO_SRV(Exception):
    def __str__(self): return 'KADM5_NO_SRV'
errors['43787529'] = KADM5_NO_SRV
class KADM5_BAD_HIST_KEY(Exception):
    def __str__(self): return 'KADM5_BAD_HIST_KEY'
errors['43787530'] = KADM5_BAD_HIST_KEY
class KADM5_NOT_INIT(Exception):
    def __str__(self): return 'KADM5_NOT_INIT'
errors['43787531'] = KADM5_NOT_INIT
class KADM5_UNK_PRINC(Exception):
    def __str__(self): return 'KADM5_UNK_PRINC'
errors['43787532'] = KADM5_UNK_PRINC
class KADM5_UNK_POLICY(Exception):
    def __str__(self): return 'KADM5_UNK_POLICY'
errors['43787533'] = KADM5_UNK_POLICY
class KADM5_BAD_MASK(Exception):
    def __str__(self): return 'KADM5_BAD_MASK'
errors['43787534'] = KADM5_BAD_MASK
class KADM5_BAD_CLASS(Exception):
    def __str__(self): return 'KADM5_BAD_CLASS'
errors['43787535'] = KADM5_BAD_CLASS
class KADM5_BAD_LENGTH(Exception):
    def __str__(self): return 'KADM5_BAD_LENGTH'
errors['43787536'] = KADM5_BAD_LENGTH
class KADM5_BAD_POLICY(Exception):
    def __str__(self): return 'KADM5_BAD_POLICY'
errors['43787537'] = KADM5_BAD_POLICY
class KADM5_BAD_PRINCIPAL(Exception):
    def __str__(self): return 'KADM5_BAD_PRINCIPAL'
errors['43787538'] = KADM5_BAD_PRINCIPAL
class KADM5_BAD_AUX_ATTR(Exception):
    def __str__(self): return 'KADM5_BAD_AUX_ATTR'
errors['43787539'] = KADM5_BAD_AUX_ATTR
class KADM5_BAD_HISTORY(Exception):
    def __str__(self): return 'KADM5_BAD_HISTORY'
errors['43787540'] = KADM5_BAD_HISTORY
class KADM5_BAD_MIN_PASS_LIFE(Exception):
    def __str__(self): return 'KADM5_BAD_MIN_PASS_LIFE'
errors['43787541'] = KADM5_BAD_MIN_PASS_LIFE
class KADM5_PASS_Q_TOOSHORT(Exception):
    def __str__(self): return 'KADM5_PASS_Q_TOOSHORT'
errors['43787542'] = KADM5_PASS_Q_TOOSHORT
class KADM5_PASS_Q_CLASS(Exception):
    def __str__(self): return 'KADM5_PASS_Q_CLASS'
errors['43787543'] = KADM5_PASS_Q_CLASS
class KADM5_PASS_Q_DICT(Exception):
    def __str__(self): return 'KADM5_PASS_Q_DICT'
errors['43787544'] = KADM5_PASS_Q_DICT
class KADM5_PASS_REUSE(Exception):
    def __str__(self): return 'KADM5_PASS_REUSE'
errors['43787545'] = KADM5_PASS_REUSE
class KADM5_PASS_TOOSOON(Exception):
    def __str__(self): return 'KADM5_PASS_TOOSOON'
errors['43787546'] = KADM5_PASS_TOOSOON
class KADM5_POLICY_REF(Exception):
    def __str__(self): return 'KADM5_POLICY_REF'
errors['43787547'] = KADM5_POLICY_REF
class KADM5_INIT(Exception):
    def __str__(self): return 'KADM5_INIT'
errors['43787548'] = KADM5_INIT
class KADM5_BAD_PASSWORD(Exception):
    def __str__(self): return 'KADM5_BAD_PASSWORD'
errors['43787549'] = KADM5_BAD_PASSWORD
class KADM5_PROTECT_PRINCIPAL(Exception):
    def __str__(self): return 'KADM5_PROTECT_PRINCIPAL'
errors['43787550'] = KADM5_PROTECT_PRINCIPAL
class KADM5_BAD_SERVER_HANDLE(Exception):
    def __str__(self): return 'KADM5_BAD_SERVER_HANDLE'
errors['43787551'] = KADM5_BAD_SERVER_HANDLE
class KADM5_BAD_STRUCT_VERSION(Exception):
    def __str__(self): return 'KADM5_BAD_STRUCT_VERSION'
errors['43787552'] = KADM5_BAD_STRUCT_VERSION
class KADM5_OLD_STRUCT_VERSION(Exception):
    def __str__(self): return 'KADM5_OLD_STRUCT_VERSION'
errors['43787553'] = KADM5_OLD_STRUCT_VERSION
class KADM5_NEW_STRUCT_VERSION(Exception):
    def __str__(self): return 'KADM5_NEW_STRUCT_VERSION'
errors['43787554'] = KADM5_NEW_STRUCT_VERSION
class KADM5_BAD_API_VERSION(Exception):
    def __str__(self): return 'KADM5_BAD_API_VERSION'
errors['43787555'] = KADM5_BAD_API_VERSION
class KADM5_OLD_LIB_API_VERSION(Exception):
    def __str__(self): return 'KADM5_OLD_LIB_API_VERSION'
errors['43787556'] = KADM5_OLD_LIB_API_VERSION
class KADM5_OLD_SERVER_API_VERSION(Exception):
    def __str__(self): return 'KADM5_OLD_SERVER_API_VERSION'
errors['43787557'] = KADM5_OLD_SERVER_API_VERSION
class KADM5_NEW_LIB_API_VERSION(Exception):
    def __str__(self): return 'KADM5_NEW_LIB_API_VERSION'
errors['43787558'] = KADM5_NEW_LIB_API_VERSION
class KADM5_NEW_SERVER_API_VERSION(Exception):
    def __str__(self): return 'KADM5_NEW_SERVER_API_VERSION'
errors['43787559'] = KADM5_NEW_SERVER_API_VERSION
class KADM5_SECURE_PRINC_MISSING(Exception):
    def __str__(self): return 'KADM5_SECURE_PRINC_MISSING'
errors['43787560'] = KADM5_SECURE_PRINC_MISSING
class KADM5_NO_RENAME_SALT(Exception):
    def __str__(self): return 'KADM5_NO_RENAME_SALT'
errors['43787561'] = KADM5_NO_RENAME_SALT
class KADM5_BAD_CLIENT_PARAMS(Exception):
    def __str__(self): return 'KADM5_BAD_CLIENT_PARAMS'
errors['43787562'] = KADM5_BAD_CLIENT_PARAMS
class KADM5_BAD_SERVER_PARAMS(Exception):
    def __str__(self): return 'KADM5_BAD_SERVER_PARAMS'
errors['43787563'] = KADM5_BAD_SERVER_PARAMS
class KADM5_AUTH_LIST(Exception):
    def __str__(self): return 'KADM5_AUTH_LIST'
errors['43787564'] = KADM5_AUTH_LIST
class KADM5_AUTH_CHANGEPW(Exception):
    def __str__(self): return 'KADM5_AUTH_CHANGEPW'
errors['43787565'] = KADM5_AUTH_CHANGEPW
class KADM5_GSS_ERROR(Exception):
    def __str__(self): return 'KADM5_GSS_ERROR'
errors['43787566'] = KADM5_GSS_ERROR
class KADM5_BAD_TL_TYPE(Exception):
    def __str__(self): return 'KADM5_BAD_TL_TYPE'
errors['43787567'] = KADM5_BAD_TL_TYPE
class KADM5_MISSING_CONF_PARAMS(Exception):
    def __str__(self): return 'KADM5_MISSING_CONF_PARAMS'
errors['43787568'] = KADM5_MISSING_CONF_PARAMS
class KADM5_BAD_SERVER_NAME(Exception):
    def __str__(self): return 'KADM5_BAD_SERVER_NAME'
errors['43787569'] = KADM5_BAD_SERVER_NAME
class KADM5_AUTH_SETKEY(Exception):
    def __str__(self): return 'KADM5_AUTH_SETKEY'
errors['43787570'] = KADM5_AUTH_SETKEY
class KADM5_SETKEY_DUP_ENCTYPES(Exception):
    def __str__(self): return 'KADM5_SETKEY_DUP_ENCTYPES'
errors['43787571'] = KADM5_SETKEY_DUP_ENCTYPES
class KADM5_SETV4KEY_INVAL_ENCTYPE(Exception):
    def __str__(self): return 'KADM5_SETV4KEY_INVAL_ENCTYPE'
errors['43787572'] = KADM5_SETV4KEY_INVAL_ENCTYPE
class KADM5_SETKEY3_ETYPE_MISMATCH(Exception):
    def __str__(self): return 'KADM5_SETKEY3_ETYPE_MISMATCH'
errors['43787573'] = KADM5_SETKEY3_ETYPE_MISMATCH
class KADM5_MISSING_KRB5_CONF_PARAMS(Exception):
    def __str__(self): return 'KADM5_MISSING_KRB5_CONF_PARAMS'
errors['43787574'] = KADM5_MISSING_KRB5_CONF_PARAMS
class ERROR_TABLE_BASE_ovk(Exception):
    def __str__(self): return 'ERROR_TABLE_BASE_ovk'
errors['43787520'] = ERROR_TABLE_BASE_ovk

class KRB5KDC_ERR_NONE(Exception):
    def __str__(self): return 'KRB5KDC_ERR_NONE'
errors['-1765328384'] = KRB5KDC_ERR_NONE
class KRB5KDC_ERR_NAME_EXP(Exception):
    def __str__(self): return 'KRB5KDC_ERR_NAME_EXP'
errors['-1765328383'] = KRB5KDC_ERR_NAME_EXP
class KRB5KDC_ERR_SERVICE_EXP(Exception):
    def __str__(self): return 'KRB5KDC_ERR_SERVICE_EXP'
errors['-1765328382'] = KRB5KDC_ERR_SERVICE_EXP
class KRB5KDC_ERR_BAD_PVNO(Exception):
    def __str__(self): return 'KRB5KDC_ERR_BAD_PVNO'
errors['-1765328381'] = KRB5KDC_ERR_BAD_PVNO
class KRB5KDC_ERR_C_OLD_MAST_KVNO(Exception):
    def __str__(self): return 'KRB5KDC_ERR_C_OLD_MAST_KVNO'
errors['-1765328380'] = KRB5KDC_ERR_C_OLD_MAST_KVNO
class KRB5KDC_ERR_S_OLD_MAST_KVNO(Exception):
    def __str__(self): return 'KRB5KDC_ERR_S_OLD_MAST_KVNO'
errors['-1765328379'] = KRB5KDC_ERR_S_OLD_MAST_KVNO
class KRB5KDC_ERR_C_PRINCIPAL_UNKNOWN(Exception):
    def __str__(self): return 'KRB5KDC_ERR_C_PRINCIPAL_UNKNOWN'
errors['-1765328378'] = KRB5KDC_ERR_C_PRINCIPAL_UNKNOWN
class KRB5KDC_ERR_S_PRINCIPAL_UNKNOWN(Exception):
    def __str__(self): return 'KRB5KDC_ERR_S_PRINCIPAL_UNKNOWN'
errors['-1765328377'] = KRB5KDC_ERR_S_PRINCIPAL_UNKNOWN
class KRB5KDC_ERR_PRINCIPAL_NOT_UNIQUE(Exception):
    def __str__(self): return 'KRB5KDC_ERR_PRINCIPAL_NOT_UNIQUE'
errors['-1765328376'] = KRB5KDC_ERR_PRINCIPAL_NOT_UNIQUE
class KRB5KDC_ERR_NULL_KEY(Exception):
    def __str__(self): return 'KRB5KDC_ERR_NULL_KEY'
errors['-1765328375'] = KRB5KDC_ERR_NULL_KEY
class KRB5KDC_ERR_CANNOT_POSTDATE(Exception):
    def __str__(self): return 'KRB5KDC_ERR_CANNOT_POSTDATE'
errors['-1765328374'] = KRB5KDC_ERR_CANNOT_POSTDATE
class KRB5KDC_ERR_NEVER_VALID(Exception):
    def __str__(self): return 'KRB5KDC_ERR_NEVER_VALID'
errors['-1765328373'] = KRB5KDC_ERR_NEVER_VALID
class KRB5KDC_ERR_POLICY(Exception):
    def __str__(self): return 'KRB5KDC_ERR_POLICY'
errors['-1765328372'] = KRB5KDC_ERR_POLICY
class KRB5KDC_ERR_BADOPTION(Exception):
    def __str__(self): return 'KRB5KDC_ERR_BADOPTION'
errors['-1765328371'] = KRB5KDC_ERR_BADOPTION
class KRB5KDC_ERR_ETYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5KDC_ERR_ETYPE_NOSUPP'
errors['-1765328370'] = KRB5KDC_ERR_ETYPE_NOSUPP
class KRB5KDC_ERR_SUMTYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5KDC_ERR_SUMTYPE_NOSUPP'
errors['-1765328369'] = KRB5KDC_ERR_SUMTYPE_NOSUPP
class KRB5KDC_ERR_PADATA_TYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5KDC_ERR_PADATA_TYPE_NOSUPP'
errors['-1765328368'] = KRB5KDC_ERR_PADATA_TYPE_NOSUPP
class KRB5KDC_ERR_TRTYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5KDC_ERR_TRTYPE_NOSUPP'
errors['-1765328367'] = KRB5KDC_ERR_TRTYPE_NOSUPP
class KRB5KDC_ERR_CLIENT_REVOKED(Exception):
    def __str__(self): return 'KRB5KDC_ERR_CLIENT_REVOKED'
errors['-1765328366'] = KRB5KDC_ERR_CLIENT_REVOKED
class KRB5KDC_ERR_SERVICE_REVOKED(Exception):
    def __str__(self): return 'KRB5KDC_ERR_SERVICE_REVOKED'
errors['-1765328365'] = KRB5KDC_ERR_SERVICE_REVOKED
class KRB5KDC_ERR_TGT_REVOKED(Exception):
    def __str__(self): return 'KRB5KDC_ERR_TGT_REVOKED'
errors['-1765328364'] = KRB5KDC_ERR_TGT_REVOKED
class KRB5KDC_ERR_CLIENT_NOTYET(Exception):
    def __str__(self): return 'KRB5KDC_ERR_CLIENT_NOTYET'
errors['-1765328363'] = KRB5KDC_ERR_CLIENT_NOTYET
class KRB5KDC_ERR_SERVICE_NOTYET(Exception):
    def __str__(self): return 'KRB5KDC_ERR_SERVICE_NOTYET'
errors['-1765328362'] = KRB5KDC_ERR_SERVICE_NOTYET
class KRB5KDC_ERR_KEY_EXP(Exception):
    def __str__(self): return 'KRB5KDC_ERR_KEY_EXP'
errors['-1765328361'] = KRB5KDC_ERR_KEY_EXP
class KRB5KDC_ERR_PREAUTH_FAILED(Exception):
    def __str__(self): return 'KRB5KDC_ERR_PREAUTH_FAILED'
errors['-1765328360'] = KRB5KDC_ERR_PREAUTH_FAILED
class KRB5KDC_ERR_PREAUTH_REQUIRED(Exception):
    def __str__(self): return 'KRB5KDC_ERR_PREAUTH_REQUIRED'
errors['-1765328359'] = KRB5KDC_ERR_PREAUTH_REQUIRED
class KRB5KDC_ERR_SERVER_NOMATCH(Exception):
    def __str__(self): return 'KRB5KDC_ERR_SERVER_NOMATCH'
errors['-1765328358'] = KRB5KDC_ERR_SERVER_NOMATCH
class KRB5PLACEHOLD_27(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_27'
errors['-1765328357'] = KRB5PLACEHOLD_27
class KRB5PLACEHOLD_28(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_28'
errors['-1765328356'] = KRB5PLACEHOLD_28
class KRB5PLACEHOLD_29(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_29'
errors['-1765328355'] = KRB5PLACEHOLD_29
class KRB5PLACEHOLD_30(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_30'
errors['-1765328354'] = KRB5PLACEHOLD_30
class KRB5KRB_AP_ERR_BAD_INTEGRITY(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BAD_INTEGRITY'
errors['-1765328353'] = KRB5KRB_AP_ERR_BAD_INTEGRITY
class KRB5KRB_AP_ERR_TKT_EXPIRED(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_TKT_EXPIRED'
errors['-1765328352'] = KRB5KRB_AP_ERR_TKT_EXPIRED
class KRB5KRB_AP_ERR_TKT_NYV(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_TKT_NYV'
errors['-1765328351'] = KRB5KRB_AP_ERR_TKT_NYV
class KRB5KRB_AP_ERR_REPEAT(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_REPEAT'
errors['-1765328350'] = KRB5KRB_AP_ERR_REPEAT
class KRB5KRB_AP_ERR_NOT_US(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_NOT_US'
errors['-1765328349'] = KRB5KRB_AP_ERR_NOT_US
class KRB5KRB_AP_ERR_BADMATCH(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BADMATCH'
errors['-1765328348'] = KRB5KRB_AP_ERR_BADMATCH
class KRB5KRB_AP_ERR_SKEW(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_SKEW'
errors['-1765328347'] = KRB5KRB_AP_ERR_SKEW
class KRB5KRB_AP_ERR_BADADDR(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BADADDR'
errors['-1765328346'] = KRB5KRB_AP_ERR_BADADDR
class KRB5KRB_AP_ERR_BADVERSION(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BADVERSION'
errors['-1765328345'] = KRB5KRB_AP_ERR_BADVERSION
class KRB5KRB_AP_ERR_MSG_TYPE(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_MSG_TYPE'
errors['-1765328344'] = KRB5KRB_AP_ERR_MSG_TYPE
class KRB5KRB_AP_ERR_MODIFIED(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_MODIFIED'
errors['-1765328343'] = KRB5KRB_AP_ERR_MODIFIED
class KRB5KRB_AP_ERR_BADORDER(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BADORDER'
errors['-1765328342'] = KRB5KRB_AP_ERR_BADORDER
class KRB5KRB_AP_ERR_ILL_CR_TKT(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_ILL_CR_TKT'
errors['-1765328341'] = KRB5KRB_AP_ERR_ILL_CR_TKT
class KRB5KRB_AP_ERR_BADKEYVER(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BADKEYVER'
errors['-1765328340'] = KRB5KRB_AP_ERR_BADKEYVER
class KRB5KRB_AP_ERR_NOKEY(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_NOKEY'
errors['-1765328339'] = KRB5KRB_AP_ERR_NOKEY
class KRB5KRB_AP_ERR_MUT_FAIL(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_MUT_FAIL'
errors['-1765328338'] = KRB5KRB_AP_ERR_MUT_FAIL
class KRB5KRB_AP_ERR_BADDIRECTION(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BADDIRECTION'
errors['-1765328337'] = KRB5KRB_AP_ERR_BADDIRECTION
class KRB5KRB_AP_ERR_METHOD(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_METHOD'
errors['-1765328336'] = KRB5KRB_AP_ERR_METHOD
class KRB5KRB_AP_ERR_BADSEQ(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_BADSEQ'
errors['-1765328335'] = KRB5KRB_AP_ERR_BADSEQ
class KRB5KRB_AP_ERR_INAPP_CKSUM(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_INAPP_CKSUM'
errors['-1765328334'] = KRB5KRB_AP_ERR_INAPP_CKSUM
class KRB5KRB_AP_PATH_NOT_ACCEPTED(Exception):
    def __str__(self): return 'KRB5KRB_AP_PATH_NOT_ACCEPTED'
errors['-1765328333'] = KRB5KRB_AP_PATH_NOT_ACCEPTED
class KRB5KRB_ERR_RESPONSE_TOO_BIG(Exception):
    def __str__(self): return 'KRB5KRB_ERR_RESPONSE_TOO_BIG'
errors['-1765328332'] = KRB5KRB_ERR_RESPONSE_TOO_BIG
class KRB5PLACEHOLD_53(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_53'
errors['-1765328331'] = KRB5PLACEHOLD_53
class KRB5PLACEHOLD_54(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_54'
errors['-1765328330'] = KRB5PLACEHOLD_54
class KRB5PLACEHOLD_55(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_55'
errors['-1765328329'] = KRB5PLACEHOLD_55
class KRB5PLACEHOLD_56(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_56'
errors['-1765328328'] = KRB5PLACEHOLD_56
class KRB5PLACEHOLD_57(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_57'
errors['-1765328327'] = KRB5PLACEHOLD_57
class KRB5PLACEHOLD_58(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_58'
errors['-1765328326'] = KRB5PLACEHOLD_58
class KRB5PLACEHOLD_59(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_59'
errors['-1765328325'] = KRB5PLACEHOLD_59
class KRB5KRB_ERR_GENERIC(Exception):
    def __str__(self): return 'KRB5KRB_ERR_GENERIC'
errors['-1765328324'] = KRB5KRB_ERR_GENERIC
class KRB5KRB_ERR_FIELD_TOOLONG(Exception):
    def __str__(self): return 'KRB5KRB_ERR_FIELD_TOOLONG'
errors['-1765328323'] = KRB5KRB_ERR_FIELD_TOOLONG
class KRB5PLACEHOLD_62(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_62'
errors['-1765328322'] = KRB5PLACEHOLD_62
class KRB5PLACEHOLD_63(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_63'
errors['-1765328321'] = KRB5PLACEHOLD_63
class KRB5PLACEHOLD_64(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_64'
errors['-1765328320'] = KRB5PLACEHOLD_64
class KRB5PLACEHOLD_65(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_65'
errors['-1765328319'] = KRB5PLACEHOLD_65
class KRB5PLACEHOLD_66(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_66'
errors['-1765328318'] = KRB5PLACEHOLD_66
class KRB5PLACEHOLD_67(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_67'
errors['-1765328317'] = KRB5PLACEHOLD_67
class KRB5PLACEHOLD_68(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_68'
errors['-1765328316'] = KRB5PLACEHOLD_68
class KRB5PLACEHOLD_69(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_69'
errors['-1765328315'] = KRB5PLACEHOLD_69
class KRB5PLACEHOLD_70(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_70'
errors['-1765328314'] = KRB5PLACEHOLD_70
class KRB5PLACEHOLD_71(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_71'
errors['-1765328313'] = KRB5PLACEHOLD_71
class KRB5PLACEHOLD_72(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_72'
errors['-1765328312'] = KRB5PLACEHOLD_72
class KRB5PLACEHOLD_73(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_73'
errors['-1765328311'] = KRB5PLACEHOLD_73
class KRB5PLACEHOLD_74(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_74'
errors['-1765328310'] = KRB5PLACEHOLD_74
class KRB5PLACEHOLD_75(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_75'
errors['-1765328309'] = KRB5PLACEHOLD_75
class KRB5PLACEHOLD_76(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_76'
errors['-1765328308'] = KRB5PLACEHOLD_76
class KRB5PLACEHOLD_77(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_77'
errors['-1765328307'] = KRB5PLACEHOLD_77
class KRB5PLACEHOLD_78(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_78'
errors['-1765328306'] = KRB5PLACEHOLD_78
class KRB5PLACEHOLD_79(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_79'
errors['-1765328305'] = KRB5PLACEHOLD_79
class KRB5PLACEHOLD_80(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_80'
errors['-1765328304'] = KRB5PLACEHOLD_80
class KRB5PLACEHOLD_81(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_81'
errors['-1765328303'] = KRB5PLACEHOLD_81
class KRB5PLACEHOLD_82(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_82'
errors['-1765328302'] = KRB5PLACEHOLD_82
class KRB5PLACEHOLD_83(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_83'
errors['-1765328301'] = KRB5PLACEHOLD_83
class KRB5PLACEHOLD_84(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_84'
errors['-1765328300'] = KRB5PLACEHOLD_84
class KRB5PLACEHOLD_85(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_85'
errors['-1765328299'] = KRB5PLACEHOLD_85
class KRB5PLACEHOLD_86(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_86'
errors['-1765328298'] = KRB5PLACEHOLD_86
class KRB5PLACEHOLD_87(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_87'
errors['-1765328297'] = KRB5PLACEHOLD_87
class KRB5PLACEHOLD_88(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_88'
errors['-1765328296'] = KRB5PLACEHOLD_88
class KRB5PLACEHOLD_89(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_89'
errors['-1765328295'] = KRB5PLACEHOLD_89
class KRB5PLACEHOLD_90(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_90'
errors['-1765328294'] = KRB5PLACEHOLD_90
class KRB5PLACEHOLD_91(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_91'
errors['-1765328293'] = KRB5PLACEHOLD_91
class KRB5PLACEHOLD_92(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_92'
errors['-1765328292'] = KRB5PLACEHOLD_92
class KRB5PLACEHOLD_93(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_93'
errors['-1765328291'] = KRB5PLACEHOLD_93
class KRB5PLACEHOLD_94(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_94'
errors['-1765328290'] = KRB5PLACEHOLD_94
class KRB5PLACEHOLD_95(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_95'
errors['-1765328289'] = KRB5PLACEHOLD_95
class KRB5PLACEHOLD_96(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_96'
errors['-1765328288'] = KRB5PLACEHOLD_96
class KRB5PLACEHOLD_97(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_97'
errors['-1765328287'] = KRB5PLACEHOLD_97
class KRB5PLACEHOLD_98(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_98'
errors['-1765328286'] = KRB5PLACEHOLD_98
class KRB5PLACEHOLD_99(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_99'
errors['-1765328285'] = KRB5PLACEHOLD_99
class KRB5PLACEHOLD_100(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_100'
errors['-1765328284'] = KRB5PLACEHOLD_100
class KRB5PLACEHOLD_101(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_101'
errors['-1765328283'] = KRB5PLACEHOLD_101
class KRB5PLACEHOLD_102(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_102'
errors['-1765328282'] = KRB5PLACEHOLD_102
class KRB5PLACEHOLD_103(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_103'
errors['-1765328281'] = KRB5PLACEHOLD_103
class KRB5PLACEHOLD_104(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_104'
errors['-1765328280'] = KRB5PLACEHOLD_104
class KRB5PLACEHOLD_105(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_105'
errors['-1765328279'] = KRB5PLACEHOLD_105
class KRB5PLACEHOLD_106(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_106'
errors['-1765328278'] = KRB5PLACEHOLD_106
class KRB5PLACEHOLD_107(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_107'
errors['-1765328277'] = KRB5PLACEHOLD_107
class KRB5PLACEHOLD_108(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_108'
errors['-1765328276'] = KRB5PLACEHOLD_108
class KRB5PLACEHOLD_109(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_109'
errors['-1765328275'] = KRB5PLACEHOLD_109
class KRB5PLACEHOLD_110(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_110'
errors['-1765328274'] = KRB5PLACEHOLD_110
class KRB5PLACEHOLD_111(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_111'
errors['-1765328273'] = KRB5PLACEHOLD_111
class KRB5PLACEHOLD_112(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_112'
errors['-1765328272'] = KRB5PLACEHOLD_112
class KRB5PLACEHOLD_113(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_113'
errors['-1765328271'] = KRB5PLACEHOLD_113
class KRB5PLACEHOLD_114(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_114'
errors['-1765328270'] = KRB5PLACEHOLD_114
class KRB5PLACEHOLD_115(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_115'
errors['-1765328269'] = KRB5PLACEHOLD_115
class KRB5PLACEHOLD_116(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_116'
errors['-1765328268'] = KRB5PLACEHOLD_116
class KRB5PLACEHOLD_117(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_117'
errors['-1765328267'] = KRB5PLACEHOLD_117
class KRB5PLACEHOLD_118(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_118'
errors['-1765328266'] = KRB5PLACEHOLD_118
class KRB5PLACEHOLD_119(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_119'
errors['-1765328265'] = KRB5PLACEHOLD_119
class KRB5PLACEHOLD_120(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_120'
errors['-1765328264'] = KRB5PLACEHOLD_120
class KRB5PLACEHOLD_121(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_121'
errors['-1765328263'] = KRB5PLACEHOLD_121
class KRB5PLACEHOLD_122(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_122'
errors['-1765328262'] = KRB5PLACEHOLD_122
class KRB5PLACEHOLD_123(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_123'
errors['-1765328261'] = KRB5PLACEHOLD_123
class KRB5PLACEHOLD_124(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_124'
errors['-1765328260'] = KRB5PLACEHOLD_124
class KRB5PLACEHOLD_125(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_125'
errors['-1765328259'] = KRB5PLACEHOLD_125
class KRB5PLACEHOLD_126(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_126'
errors['-1765328258'] = KRB5PLACEHOLD_126
class KRB5PLACEHOLD_127(Exception):
    def __str__(self): return 'KRB5PLACEHOLD_127'
errors['-1765328257'] = KRB5PLACEHOLD_127
class KRB5_ERR_RCSID(Exception):
    def __str__(self): return 'KRB5_ERR_RCSID'
errors['-1765328256'] = KRB5_ERR_RCSID
class KRB5_LIBOS_BADLOCKFLAG(Exception):
    def __str__(self): return 'KRB5_LIBOS_BADLOCKFLAG'
errors['-1765328255'] = KRB5_LIBOS_BADLOCKFLAG
class KRB5_LIBOS_CANTREADPWD(Exception):
    def __str__(self): return 'KRB5_LIBOS_CANTREADPWD'
errors['-1765328254'] = KRB5_LIBOS_CANTREADPWD
class KRB5_LIBOS_BADPWDMATCH(Exception):
    def __str__(self): return 'KRB5_LIBOS_BADPWDMATCH'
errors['-1765328253'] = KRB5_LIBOS_BADPWDMATCH
class KRB5_LIBOS_PWDINTR(Exception):
    def __str__(self): return 'KRB5_LIBOS_PWDINTR'
errors['-1765328252'] = KRB5_LIBOS_PWDINTR
class KRB5_PARSE_ILLCHAR(Exception):
    def __str__(self): return 'KRB5_PARSE_ILLCHAR'
errors['-1765328251'] = KRB5_PARSE_ILLCHAR
class KRB5_PARSE_MALFORMED(Exception):
    def __str__(self): return 'KRB5_PARSE_MALFORMED'
errors['-1765328250'] = KRB5_PARSE_MALFORMED
class KRB5_CONFIG_CANTOPEN(Exception):
    def __str__(self): return 'KRB5_CONFIG_CANTOPEN'
errors['-1765328249'] = KRB5_CONFIG_CANTOPEN
class KRB5_CONFIG_BADFORMAT(Exception):
    def __str__(self): return 'KRB5_CONFIG_BADFORMAT'
errors['-1765328248'] = KRB5_CONFIG_BADFORMAT
class KRB5_CONFIG_NOTENUFSPACE(Exception):
    def __str__(self): return 'KRB5_CONFIG_NOTENUFSPACE'
errors['-1765328247'] = KRB5_CONFIG_NOTENUFSPACE
class KRB5_BADMSGTYPE(Exception):
    def __str__(self): return 'KRB5_BADMSGTYPE'
errors['-1765328246'] = KRB5_BADMSGTYPE
class KRB5_CC_BADNAME(Exception):
    def __str__(self): return 'KRB5_CC_BADNAME'
errors['-1765328245'] = KRB5_CC_BADNAME
class KRB5_CC_UNKNOWN_TYPE(Exception):
    def __str__(self): return 'KRB5_CC_UNKNOWN_TYPE'
errors['-1765328244'] = KRB5_CC_UNKNOWN_TYPE
class KRB5_CC_NOTFOUND(Exception):
    def __str__(self): return 'KRB5_CC_NOTFOUND'
errors['-1765328243'] = KRB5_CC_NOTFOUND
class KRB5_CC_END(Exception):
    def __str__(self): return 'KRB5_CC_END'
errors['-1765328242'] = KRB5_CC_END
class KRB5_NO_TKT_SUPPLIED(Exception):
    def __str__(self): return 'KRB5_NO_TKT_SUPPLIED'
errors['-1765328241'] = KRB5_NO_TKT_SUPPLIED
class KRB5KRB_AP_WRONG_PRINC(Exception):
    def __str__(self): return 'KRB5KRB_AP_WRONG_PRINC'
errors['-1765328240'] = KRB5KRB_AP_WRONG_PRINC
class KRB5KRB_AP_ERR_TKT_INVALID(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_TKT_INVALID'
errors['-1765328239'] = KRB5KRB_AP_ERR_TKT_INVALID
class KRB5_PRINC_NOMATCH(Exception):
    def __str__(self): return 'KRB5_PRINC_NOMATCH'
errors['-1765328238'] = KRB5_PRINC_NOMATCH
class KRB5_KDCREP_MODIFIED(Exception):
    def __str__(self): return 'KRB5_KDCREP_MODIFIED'
errors['-1765328237'] = KRB5_KDCREP_MODIFIED
class KRB5_KDCREP_SKEW(Exception):
    def __str__(self): return 'KRB5_KDCREP_SKEW'
errors['-1765328236'] = KRB5_KDCREP_SKEW
class KRB5_IN_TKT_REALM_MISMATCH(Exception):
    def __str__(self): return 'KRB5_IN_TKT_REALM_MISMATCH'
errors['-1765328235'] = KRB5_IN_TKT_REALM_MISMATCH
class KRB5_PROG_ETYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5_PROG_ETYPE_NOSUPP'
errors['-1765328234'] = KRB5_PROG_ETYPE_NOSUPP
class KRB5_PROG_KEYTYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5_PROG_KEYTYPE_NOSUPP'
errors['-1765328233'] = KRB5_PROG_KEYTYPE_NOSUPP
class KRB5_WRONG_ETYPE(Exception):
    def __str__(self): return 'KRB5_WRONG_ETYPE'
errors['-1765328232'] = KRB5_WRONG_ETYPE
class KRB5_PROG_SUMTYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5_PROG_SUMTYPE_NOSUPP'
errors['-1765328231'] = KRB5_PROG_SUMTYPE_NOSUPP
class KRB5_REALM_UNKNOWN(Exception):
    def __str__(self): return 'KRB5_REALM_UNKNOWN'
errors['-1765328230'] = KRB5_REALM_UNKNOWN
class KRB5_SERVICE_UNKNOWN(Exception):
    def __str__(self): return 'KRB5_SERVICE_UNKNOWN'
errors['-1765328229'] = KRB5_SERVICE_UNKNOWN
class KRB5_KDC_UNREACH(Exception):
    def __str__(self): return 'KRB5_KDC_UNREACH'
errors['-1765328228'] = KRB5_KDC_UNREACH
class KRB5_NO_LOCALNAME(Exception):
    def __str__(self): return 'KRB5_NO_LOCALNAME'
errors['-1765328227'] = KRB5_NO_LOCALNAME
class KRB5_MUTUAL_FAILED(Exception):
    def __str__(self): return 'KRB5_MUTUAL_FAILED'
errors['-1765328226'] = KRB5_MUTUAL_FAILED
class KRB5_RC_TYPE_EXISTS(Exception):
    def __str__(self): return 'KRB5_RC_TYPE_EXISTS'
errors['-1765328225'] = KRB5_RC_TYPE_EXISTS
class KRB5_RC_MALLOC(Exception):
    def __str__(self): return 'KRB5_RC_MALLOC'
errors['-1765328224'] = KRB5_RC_MALLOC
class KRB5_RC_TYPE_NOTFOUND(Exception):
    def __str__(self): return 'KRB5_RC_TYPE_NOTFOUND'
errors['-1765328223'] = KRB5_RC_TYPE_NOTFOUND
class KRB5_RC_UNKNOWN(Exception):
    def __str__(self): return 'KRB5_RC_UNKNOWN'
errors['-1765328222'] = KRB5_RC_UNKNOWN
class KRB5_RC_REPLAY(Exception):
    def __str__(self): return 'KRB5_RC_REPLAY'
errors['-1765328221'] = KRB5_RC_REPLAY
class KRB5_RC_IO(Exception):
    def __str__(self): return 'KRB5_RC_IO'
errors['-1765328220'] = KRB5_RC_IO
class KRB5_RC_NOIO(Exception):
    def __str__(self): return 'KRB5_RC_NOIO'
errors['-1765328219'] = KRB5_RC_NOIO
class KRB5_RC_PARSE(Exception):
    def __str__(self): return 'KRB5_RC_PARSE'
errors['-1765328218'] = KRB5_RC_PARSE
class KRB5_RC_IO_EOF(Exception):
    def __str__(self): return 'KRB5_RC_IO_EOF'
errors['-1765328217'] = KRB5_RC_IO_EOF
class KRB5_RC_IO_MALLOC(Exception):
    def __str__(self): return 'KRB5_RC_IO_MALLOC'
errors['-1765328216'] = KRB5_RC_IO_MALLOC
class KRB5_RC_IO_PERM(Exception):
    def __str__(self): return 'KRB5_RC_IO_PERM'
errors['-1765328215'] = KRB5_RC_IO_PERM
class KRB5_RC_IO_IO(Exception):
    def __str__(self): return 'KRB5_RC_IO_IO'
errors['-1765328214'] = KRB5_RC_IO_IO
class KRB5_RC_IO_UNKNOWN(Exception):
    def __str__(self): return 'KRB5_RC_IO_UNKNOWN'
errors['-1765328213'] = KRB5_RC_IO_UNKNOWN
class KRB5_RC_IO_SPACE(Exception):
    def __str__(self): return 'KRB5_RC_IO_SPACE'
errors['-1765328212'] = KRB5_RC_IO_SPACE
class KRB5_TRANS_CANTOPEN(Exception):
    def __str__(self): return 'KRB5_TRANS_CANTOPEN'
errors['-1765328211'] = KRB5_TRANS_CANTOPEN
class KRB5_TRANS_BADFORMAT(Exception):
    def __str__(self): return 'KRB5_TRANS_BADFORMAT'
errors['-1765328210'] = KRB5_TRANS_BADFORMAT
class KRB5_LNAME_CANTOPEN(Exception):
    def __str__(self): return 'KRB5_LNAME_CANTOPEN'
errors['-1765328209'] = KRB5_LNAME_CANTOPEN
class KRB5_LNAME_NOTRANS(Exception):
    def __str__(self): return 'KRB5_LNAME_NOTRANS'
errors['-1765328208'] = KRB5_LNAME_NOTRANS
class KRB5_LNAME_BADFORMAT(Exception):
    def __str__(self): return 'KRB5_LNAME_BADFORMAT'
errors['-1765328207'] = KRB5_LNAME_BADFORMAT
class KRB5_CRYPTO_INTERNAL(Exception):
    def __str__(self): return 'KRB5_CRYPTO_INTERNAL'
errors['-1765328206'] = KRB5_CRYPTO_INTERNAL
class KRB5_KT_BADNAME(Exception):
    def __str__(self): return 'KRB5_KT_BADNAME'
errors['-1765328205'] = KRB5_KT_BADNAME
class KRB5_KT_UNKNOWN_TYPE(Exception):
    def __str__(self): return 'KRB5_KT_UNKNOWN_TYPE'
errors['-1765328204'] = KRB5_KT_UNKNOWN_TYPE
class KRB5_KT_NOTFOUND(Exception):
    def __str__(self): return 'KRB5_KT_NOTFOUND'
errors['-1765328203'] = KRB5_KT_NOTFOUND
class KRB5_KT_END(Exception):
    def __str__(self): return 'KRB5_KT_END'
errors['-1765328202'] = KRB5_KT_END
class KRB5_KT_NOWRITE(Exception):
    def __str__(self): return 'KRB5_KT_NOWRITE'
errors['-1765328201'] = KRB5_KT_NOWRITE
class KRB5_KT_IOERR(Exception):
    def __str__(self): return 'KRB5_KT_IOERR'
errors['-1765328200'] = KRB5_KT_IOERR
class KRB5_NO_TKT_IN_RLM(Exception):
    def __str__(self): return 'KRB5_NO_TKT_IN_RLM'
errors['-1765328199'] = KRB5_NO_TKT_IN_RLM
class KRB5DES_BAD_KEYPAR(Exception):
    def __str__(self): return 'KRB5DES_BAD_KEYPAR'
errors['-1765328198'] = KRB5DES_BAD_KEYPAR
class KRB5DES_WEAK_KEY(Exception):
    def __str__(self): return 'KRB5DES_WEAK_KEY'
errors['-1765328197'] = KRB5DES_WEAK_KEY
class KRB5_BAD_ENCTYPE(Exception):
    def __str__(self): return 'KRB5_BAD_ENCTYPE'
errors['-1765328196'] = KRB5_BAD_ENCTYPE
class KRB5_BAD_KEYSIZE(Exception):
    def __str__(self): return 'KRB5_BAD_KEYSIZE'
errors['-1765328195'] = KRB5_BAD_KEYSIZE
class KRB5_BAD_MSIZE(Exception):
    def __str__(self): return 'KRB5_BAD_MSIZE'
errors['-1765328194'] = KRB5_BAD_MSIZE
class KRB5_CC_TYPE_EXISTS(Exception):
    def __str__(self): return 'KRB5_CC_TYPE_EXISTS'
errors['-1765328193'] = KRB5_CC_TYPE_EXISTS
class KRB5_KT_TYPE_EXISTS(Exception):
    def __str__(self): return 'KRB5_KT_TYPE_EXISTS'
errors['-1765328192'] = KRB5_KT_TYPE_EXISTS
class KRB5_CC_IO(Exception):
    def __str__(self): return 'KRB5_CC_IO'
errors['-1765328191'] = KRB5_CC_IO
class KRB5_FCC_PERM(Exception):
    def __str__(self): return 'KRB5_FCC_PERM'
errors['-1765328190'] = KRB5_FCC_PERM
class KRB5_FCC_NOFILE(Exception):
    def __str__(self): return 'KRB5_FCC_NOFILE'
errors['-1765328189'] = KRB5_FCC_NOFILE
class KRB5_FCC_INTERNAL(Exception):
    def __str__(self): return 'KRB5_FCC_INTERNAL'
errors['-1765328188'] = KRB5_FCC_INTERNAL
class KRB5_CC_WRITE(Exception):
    def __str__(self): return 'KRB5_CC_WRITE'
errors['-1765328187'] = KRB5_CC_WRITE
class KRB5_CC_NOMEM(Exception):
    def __str__(self): return 'KRB5_CC_NOMEM'
errors['-1765328186'] = KRB5_CC_NOMEM
class KRB5_CC_FORMAT(Exception):
    def __str__(self): return 'KRB5_CC_FORMAT'
errors['-1765328185'] = KRB5_CC_FORMAT
class KRB5_CC_NOT_KTYPE(Exception):
    def __str__(self): return 'KRB5_CC_NOT_KTYPE'
errors['-1765328184'] = KRB5_CC_NOT_KTYPE
class KRB5_INVALID_FLAGS(Exception):
    def __str__(self): return 'KRB5_INVALID_FLAGS'
errors['-1765328183'] = KRB5_INVALID_FLAGS
class KRB5_NO_2ND_TKT(Exception):
    def __str__(self): return 'KRB5_NO_2ND_TKT'
errors['-1765328182'] = KRB5_NO_2ND_TKT
class KRB5_NOCREDS_SUPPLIED(Exception):
    def __str__(self): return 'KRB5_NOCREDS_SUPPLIED'
errors['-1765328181'] = KRB5_NOCREDS_SUPPLIED
class KRB5_SENDAUTH_BADAUTHVERS(Exception):
    def __str__(self): return 'KRB5_SENDAUTH_BADAUTHVERS'
errors['-1765328180'] = KRB5_SENDAUTH_BADAUTHVERS
class KRB5_SENDAUTH_BADAPPLVERS(Exception):
    def __str__(self): return 'KRB5_SENDAUTH_BADAPPLVERS'
errors['-1765328179'] = KRB5_SENDAUTH_BADAPPLVERS
class KRB5_SENDAUTH_BADRESPONSE(Exception):
    def __str__(self): return 'KRB5_SENDAUTH_BADRESPONSE'
errors['-1765328178'] = KRB5_SENDAUTH_BADRESPONSE
class KRB5_SENDAUTH_REJECTED(Exception):
    def __str__(self): return 'KRB5_SENDAUTH_REJECTED'
errors['-1765328177'] = KRB5_SENDAUTH_REJECTED
class KRB5_PREAUTH_BAD_TYPE(Exception):
    def __str__(self): return 'KRB5_PREAUTH_BAD_TYPE'
errors['-1765328176'] = KRB5_PREAUTH_BAD_TYPE
class KRB5_PREAUTH_NO_KEY(Exception):
    def __str__(self): return 'KRB5_PREAUTH_NO_KEY'
errors['-1765328175'] = KRB5_PREAUTH_NO_KEY
class KRB5_PREAUTH_FAILED(Exception):
    def __str__(self): return 'KRB5_PREAUTH_FAILED'
errors['-1765328174'] = KRB5_PREAUTH_FAILED
class KRB5_RCACHE_BADVNO(Exception):
    def __str__(self): return 'KRB5_RCACHE_BADVNO'
errors['-1765328173'] = KRB5_RCACHE_BADVNO
class KRB5_CCACHE_BADVNO(Exception):
    def __str__(self): return 'KRB5_CCACHE_BADVNO'
errors['-1765328172'] = KRB5_CCACHE_BADVNO
class KRB5_KEYTAB_BADVNO(Exception):
    def __str__(self): return 'KRB5_KEYTAB_BADVNO'
errors['-1765328171'] = KRB5_KEYTAB_BADVNO
class KRB5_PROG_ATYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5_PROG_ATYPE_NOSUPP'
errors['-1765328170'] = KRB5_PROG_ATYPE_NOSUPP
class KRB5_RC_REQUIRED(Exception):
    def __str__(self): return 'KRB5_RC_REQUIRED'
errors['-1765328169'] = KRB5_RC_REQUIRED
class KRB5_ERR_BAD_HOSTNAME(Exception):
    def __str__(self): return 'KRB5_ERR_BAD_HOSTNAME'
errors['-1765328168'] = KRB5_ERR_BAD_HOSTNAME
class KRB5_ERR_HOST_REALM_UNKNOWN(Exception):
    def __str__(self): return 'KRB5_ERR_HOST_REALM_UNKNOWN'
errors['-1765328167'] = KRB5_ERR_HOST_REALM_UNKNOWN
class KRB5_SNAME_UNSUPP_NAMETYPE(Exception):
    def __str__(self): return 'KRB5_SNAME_UNSUPP_NAMETYPE'
errors['-1765328166'] = KRB5_SNAME_UNSUPP_NAMETYPE
class KRB5KRB_AP_ERR_V4_REPLY(Exception):
    def __str__(self): return 'KRB5KRB_AP_ERR_V4_REPLY'
errors['-1765328165'] = KRB5KRB_AP_ERR_V4_REPLY
class KRB5_REALM_CANT_RESOLVE(Exception):
    def __str__(self): return 'KRB5_REALM_CANT_RESOLVE'
errors['-1765328164'] = KRB5_REALM_CANT_RESOLVE
class KRB5_TKT_NOT_FORWARDABLE(Exception):
    def __str__(self): return 'KRB5_TKT_NOT_FORWARDABLE'
errors['-1765328163'] = KRB5_TKT_NOT_FORWARDABLE
class KRB5_FWD_BAD_PRINCIPAL(Exception):
    def __str__(self): return 'KRB5_FWD_BAD_PRINCIPAL'
errors['-1765328162'] = KRB5_FWD_BAD_PRINCIPAL
class KRB5_GET_IN_TKT_LOOP(Exception):
    def __str__(self): return 'KRB5_GET_IN_TKT_LOOP'
errors['-1765328161'] = KRB5_GET_IN_TKT_LOOP
class KRB5_CONFIG_NODEFREALM(Exception):
    def __str__(self): return 'KRB5_CONFIG_NODEFREALM'
errors['-1765328160'] = KRB5_CONFIG_NODEFREALM
class KRB5_SAM_UNSUPPORTED(Exception):
    def __str__(self): return 'KRB5_SAM_UNSUPPORTED'
errors['-1765328159'] = KRB5_SAM_UNSUPPORTED
class KRB5_SAM_INVALID_ETYPE(Exception):
    def __str__(self): return 'KRB5_SAM_INVALID_ETYPE'
errors['-1765328158'] = KRB5_SAM_INVALID_ETYPE
class KRB5_SAM_NO_CHECKSUM(Exception):
    def __str__(self): return 'KRB5_SAM_NO_CHECKSUM'
errors['-1765328157'] = KRB5_SAM_NO_CHECKSUM
class KRB5_SAM_BAD_CHECKSUM(Exception):
    def __str__(self): return 'KRB5_SAM_BAD_CHECKSUM'
errors['-1765328156'] = KRB5_SAM_BAD_CHECKSUM
class KRB5_KT_NAME_TOOLONG(Exception):
    def __str__(self): return 'KRB5_KT_NAME_TOOLONG'
errors['-1765328155'] = KRB5_KT_NAME_TOOLONG
class KRB5_KT_KVNONOTFOUND(Exception):
    def __str__(self): return 'KRB5_KT_KVNONOTFOUND'
errors['-1765328154'] = KRB5_KT_KVNONOTFOUND
class KRB5_APPL_EXPIRED(Exception):
    def __str__(self): return 'KRB5_APPL_EXPIRED'
errors['-1765328153'] = KRB5_APPL_EXPIRED
class KRB5_LIB_EXPIRED(Exception):
    def __str__(self): return 'KRB5_LIB_EXPIRED'
errors['-1765328152'] = KRB5_LIB_EXPIRED
class KRB5_CHPW_PWDNULL(Exception):
    def __str__(self): return 'KRB5_CHPW_PWDNULL'
errors['-1765328151'] = KRB5_CHPW_PWDNULL
class KRB5_CHPW_FAIL(Exception):
    def __str__(self): return 'KRB5_CHPW_FAIL'
errors['-1765328150'] = KRB5_CHPW_FAIL
class KRB5_KT_FORMAT(Exception):
    def __str__(self): return 'KRB5_KT_FORMAT'
errors['-1765328149'] = KRB5_KT_FORMAT
class KRB5_NOPERM_ETYPE(Exception):
    def __str__(self): return 'KRB5_NOPERM_ETYPE'
errors['-1765328148'] = KRB5_NOPERM_ETYPE
class KRB5_CONFIG_ETYPE_NOSUPP(Exception):
    def __str__(self): return 'KRB5_CONFIG_ETYPE_NOSUPP'
errors['-1765328147'] = KRB5_CONFIG_ETYPE_NOSUPP
class KRB5_OBSOLETE_FN(Exception):
    def __str__(self): return 'KRB5_OBSOLETE_FN'
errors['-1765328146'] = KRB5_OBSOLETE_FN
class KRB5_EAI_FAIL(Exception):
    def __str__(self): return 'KRB5_EAI_FAIL'
errors['-1765328145'] = KRB5_EAI_FAIL
class KRB5_EAI_NODATA(Exception):
    def __str__(self): return 'KRB5_EAI_NODATA'
errors['-1765328144'] = KRB5_EAI_NODATA
class KRB5_EAI_NONAME(Exception):
    def __str__(self): return 'KRB5_EAI_NONAME'
errors['-1765328143'] = KRB5_EAI_NONAME
class KRB5_EAI_SERVICE(Exception):
    def __str__(self): return 'KRB5_EAI_SERVICE'
errors['-1765328142'] = KRB5_EAI_SERVICE
class KRB5_ERR_NUMERIC_REALM(Exception):
    def __str__(self): return 'KRB5_ERR_NUMERIC_REALM'
errors['-1765328141'] = KRB5_ERR_NUMERIC_REALM
class KRB5_ERR_BAD_S2K_PARAMS(Exception):
    def __str__(self): return 'KRB5_ERR_BAD_S2K_PARAMS'
errors['-1765328140'] = KRB5_ERR_BAD_S2K_PARAMS
class KRB5_ERR_NO_SERVICE(Exception):
    def __str__(self): return 'KRB5_ERR_NO_SERVICE'
errors['-1765328139'] = KRB5_ERR_NO_SERVICE
class KRB5_CC_READONLY(Exception):
    def __str__(self): return 'KRB5_CC_READONLY'
errors['-1765328138'] = KRB5_CC_READONLY
class KRB5_CC_NOSUPP(Exception):
    def __str__(self): return 'KRB5_CC_NOSUPP'
errors['-1765328137'] = KRB5_CC_NOSUPP
class ERROR_TABLE_BASE_krb5(Exception):
    def __str__(self): return 'ERROR_TABLE_BASE_krb5'
errors['-1765328384'] = ERROR_TABLE_BASE_krb5