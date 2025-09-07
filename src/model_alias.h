// Transitional alias header to map LN-proper names to current GGIO-based model
// Switch to the SCL-generated model by redefining these macros accordingly.

#ifndef MODEL_ALIAS_H
#define MODEL_ALIAS_H

// Data attribute aliases (server-side symbols)
// Trip result (PTRC1.Tr)
#define IEDMODEL_LD0_PTRC1_Tr_stVal        IEDMODEL_GenericIO_PTRC1_Tr_stVal
#define IEDMODEL_LD0_PTRC1_Tr_q            IEDMODEL_GenericIO_PTRC1_Tr_q
#define IEDMODEL_LD0_PTRC1_Tr_t            IEDMODEL_GenericIO_PTRC1_Tr_t
// DO for control handler binding (use CSWI1.Op as control object)
#define IEDMODEL_LD0_PTRC1_Tr_DO           IEDMODEL_GenericIO_CSWI1_Op

// Breaker position (XCBR1.Pos)
#define IEDMODEL_LD0_XCBR1_Pos_stVal       IEDMODEL_GenericIO_XCBR1_Pos_stVal
#define IEDMODEL_LD0_XCBR1_Pos_q           IEDMODEL_GenericIO_XCBR1_Pos_q
#define IEDMODEL_LD0_XCBR1_Pos_t           IEDMODEL_GenericIO_XCBR1_Pos_t

// Overcurrent (PTOC1)
#define IEDMODEL_LD0_PTOC1_Op_stVal        IEDMODEL_GenericIO_PTOC1_Op_stVal
#define IEDMODEL_LD0_PTOC1_Op_q            IEDMODEL_GenericIO_PTOC1_Op_q
#define IEDMODEL_LD0_PTOC1_Str_stVal       IEDMODEL_GenericIO_PTOC1_Str_stVal
#define IEDMODEL_LD0_PTOC1_Str_q           IEDMODEL_GenericIO_PTOC1_Str_q
#define IEDMODEL_LD0_PTOC1_Op_t            IEDMODEL_GenericIO_PTOC1_Op_t
#define IEDMODEL_LD0_PTOC1_Str_t           IEDMODEL_GenericIO_PTOC1_Str_t

// Measurements (MMXU1)
#define IEDMODEL_LD0_MMXU1_PhV_mag_f       IEDMODEL_GenericIO_MMXU1_PhV_mag_f
#define IEDMODEL_LD0_MMXU1_Amp_mag_f       IEDMODEL_GenericIO_MMXU1_Amp_mag_f
#define IEDMODEL_LD0_MMXU1_Hz_mag_f        IEDMODEL_GenericIO_MMXU1_Hz_mag_f

// String object references used by HMI client (transitional mapping)
#define REF_MMXU_VOLT      "simpleIOGenericIO/MMXU1.PhV.mag.f"
#define REF_MMXU_CURR      "simpleIOGenericIO/MMXU1.Amp.mag.f"
#define REF_MMXU_FREQ      "simpleIOGenericIO/MMXU1.Hz.mag.f"
#define REF_PTOC_STR       "simpleIOGenericIO/PTOC1.Str.stVal"
#define REF_PTOC_OP        "simpleIOGenericIO/PTOC1.Op.stVal"
#define REF_PTRC_TR        "simpleIOGenericIO/PTRC1.Tr.stVal"
#define REF_XCBR_POS       "simpleIOGenericIO/XCBR1.Pos.stVal"

#endif // MODEL_ALIAS_H
