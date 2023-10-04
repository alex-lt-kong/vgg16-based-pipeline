#ifndef InternalState_hpp
#define InternalState_hpp

#include "oatpp/core/Types.hpp"
#include "oatpp/core/macro/codegen.hpp"

#include OATPP_CODEGEN_BEGIN(DTO)

class InternalStateDto : public oatpp::DTO {

  DTO_INIT(InternalStateDto, DTO)

  DTO_FIELD(Int32, predictionIntervalMs, "predictionIntervalMs");
  DTO_FIELD_INFO(modelIds) {
    info->description = "The IDs of the ensemble of CNN models";
  }
  DTO_FIELD(String, modelIds, "modelIds");
  DTO_FIELD(UInt32, image_queue_size, "imageQueueSize");
  DTO_FIELD_INFO(inference_duration_stats) {
    info->description = "Percentiles of time (in us) needed to infer one image";
  }
  DTO_FIELD(List<Fields<Float64>>, inference_duration_stats,
            "inferenceDurationStats");
};

#include OATPP_CODEGEN_END(DTO)

#endif /* InternalState_hpp */
