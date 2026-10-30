// SPDX-License-Identifier: MIT
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <initguid.h>
#include <directx/d3d12.h>
#include <d3d11_4.h>
#include <dxgi1_6.h>
#include <wrl/client.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <vector>
using Microsoft::WRL::ComPtr;
#define GET(type, p) IID_##type, reinterpret_cast<void**>((p).ReleaseAndGetAddressOf())
static void Check(HRESULT h, const char* operation) {
    if (FAILED(h)) { std::cerr<<operation<<": HRESULT 0x"<<std::hex<<static_cast<unsigned long>(h)<<'\n'; throw std::runtime_error(operation); }
}
#define HR(x) Check((x), #x)
struct Handle {
    HANDLE h=nullptr;
    Handle()=default; Handle(const Handle&)=delete; Handle& operator=(const Handle&)=delete;
    ~Handle(){if(h) CloseHandle(h);}
};
static ComPtr<ID3D12Resource> Buffer(ID3D12Device* device, UINT64 bytes, bool upload, D3D12_RESOURCE_STATES state) {
    D3D12_HEAP_PROPERTIES heap{};
    heap.Type=upload?D3D12_HEAP_TYPE_UPLOAD:D3D12_HEAP_TYPE_DEFAULT;
    heap.CreationNodeMask=heap.VisibleNodeMask=1;
    D3D12_RESOURCE_DESC d{};
    d.Dimension=D3D12_RESOURCE_DIMENSION_BUFFER; d.Width=(bytes+255)&~UINT64(255);
    d.Height=d.DepthOrArraySize=d.MipLevels=d.SampleDesc.Count=1;
    d.Layout=D3D12_TEXTURE_LAYOUT_ROW_MAJOR;
    d.Flags=upload?D3D12_RESOURCE_FLAG_NONE:D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS;
    ComPtr<ID3D12Resource> p;
    HR(device->CreateCommittedResource(&heap,D3D12_HEAP_FLAG_NONE,&d,state,nullptr,GET(ID3D12Resource,p)));
    return p;
}
static void Upload(ID3D12Resource* p,const void* data,size_t bytes){
    void* mapped=nullptr; D3D12_RANGE empty{0,0},written{0,bytes};
    HR(p->Map(0,&empty,&mapped)); std::memcpy(mapped,data,bytes); p->Unmap(0,&written);
}
static int Run(){
    std::cout<<"RTLab: DXR 1.1, BLAS/TLAS, DX11/12 shared texture and fences\n";
    ComPtr<IDXGIFactory6> factory; HR(CreateDXGIFactory1(GET(IDXGIFactory6,factory)));
    ComPtr<IDXGIAdapter1> adapter; ComPtr<ID3D12Device5> device;
    for(UINT i=0;;++i){
        ComPtr<IDXGIAdapter1> candidate;
        HRESULT h=factory->EnumAdapterByGpuPreference(i,DXGI_GPU_PREFERENCE_HIGH_PERFORMANCE,GET(IDXGIAdapter1,candidate));
        if(h==DXGI_ERROR_NOT_FOUND) break;
        HR(h);
        DXGI_ADAPTER_DESC1 d{}; HR(candidate->GetDesc1(&d));
        if(d.Flags & DXGI_ADAPTER_FLAG_SOFTWARE) continue;
        ComPtr<ID3D12Device5> dev;
        if(FAILED(D3D12CreateDevice(candidate.Get(),D3D_FEATURE_LEVEL_12_0,GET(ID3D12Device5,dev)))) continue;
        D3D12_FEATURE_DATA_D3D12_OPTIONS5 options{};
        if(FAILED(dev->CheckFeatureSupport(D3D12_FEATURE_D3D12_OPTIONS5,&options,sizeof(options))) || options.RaytracingTier<D3D12_RAYTRACING_TIER_1_1) continue;
        adapter=candidate; device=dev; std::wcout<<L"Adapter: "<<d.Description<<L'\n'; break;
    }
    if(!device){std::cerr<<"SKIPPED: no hardware DXR 1.1 adapter; NOT a GPU test pass\n";return 77;}
    ComPtr<ID3D11Device> base; ComPtr<ID3D11DeviceContext> contextBase;
    HR(D3D11CreateDevice(adapter.Get(),D3D_DRIVER_TYPE_UNKNOWN,nullptr,0,nullptr,0,D3D11_SDK_VERSION,&base,nullptr,&contextBase));
    ComPtr<ID3D11Device5> device11; ComPtr<ID3D11DeviceContext4> context;
    HR(base->QueryInterface(GET(ID3D11Device5,device11)));
    HR(contextBase->QueryInterface(GET(ID3D11DeviceContext4,context)));
    ComPtr<ID3D12CommandQueue> queue; D3D12_COMMAND_QUEUE_DESC qd{};
    HR(device->CreateCommandQueue(&qd,GET(ID3D12CommandQueue,queue)));
    ComPtr<ID3D12CommandAllocator> allocator;
    HR(device->CreateCommandAllocator(D3D12_COMMAND_LIST_TYPE_DIRECT,GET(ID3D12CommandAllocator,allocator)));
    ComPtr<ID3D12GraphicsCommandList4> commands;
    HR(device->CreateCommandList(0,D3D12_COMMAND_LIST_TYPE_DIRECT,allocator.Get(),nullptr,GET(ID3D12GraphicsCommandList4,commands)));
    const float vertices[]={-.5f,-.5f,0,.5f,-.5f,0,.5f,.5f,0,-.5f,-.5f,0,.5f,.5f,0,-.5f,.5f,0};
    auto vb=Buffer(device.Get(),sizeof(vertices),true,D3D12_RESOURCE_STATE_GENERIC_READ); Upload(vb.Get(),vertices,sizeof(vertices));
    D3D12_RAYTRACING_GEOMETRY_DESC geo{}; geo.Type=D3D12_RAYTRACING_GEOMETRY_TYPE_TRIANGLES; geo.Flags=D3D12_RAYTRACING_GEOMETRY_FLAG_OPAQUE;
    geo.Triangles.VertexBuffer={vb->GetGPUVirtualAddress(),12};geo.Triangles.VertexCount=6;geo.Triangles.VertexFormat=DXGI_FORMAT_R32G32B32_FLOAT;
    D3D12_BUILD_RAYTRACING_ACCELERATION_STRUCTURE_INPUTS bottom{},top{};
    bottom.Type=D3D12_RAYTRACING_ACCELERATION_STRUCTURE_TYPE_BOTTOM_LEVEL;bottom.DescsLayout=D3D12_ELEMENTS_LAYOUT_ARRAY;bottom.NumDescs=1;bottom.pGeometryDescs=&geo;
    bottom.Flags=D3D12_RAYTRACING_ACCELERATION_STRUCTURE_BUILD_FLAG_PREFER_FAST_TRACE;
    top.Type=D3D12_RAYTRACING_ACCELERATION_STRUCTURE_TYPE_TOP_LEVEL;top.DescsLayout=D3D12_ELEMENTS_LAYOUT_ARRAY;top.NumDescs=1;top.Flags=bottom.Flags;
    D3D12_RAYTRACING_ACCELERATION_STRUCTURE_PREBUILD_INFO bi{},ti{};
    device->GetRaytracingAccelerationStructurePrebuildInfo(&bottom,&bi);device->GetRaytracingAccelerationStructurePrebuildInfo(&top,&ti);
    if(!bi.ResultDataMaxSizeInBytes || !ti.ResultDataMaxSizeInBytes) throw std::runtime_error("Empty prebuild sizes");
    auto scratch=Buffer(device.Get(),(std::max)(bi.ScratchDataSizeInBytes,ti.ScratchDataSizeInBytes),false,D3D12_RESOURCE_STATE_UNORDERED_ACCESS);
    auto blas=Buffer(device.Get(),bi.ResultDataMaxSizeInBytes,false,D3D12_RESOURCE_STATE_RAYTRACING_ACCELERATION_STRUCTURE);
    auto tlas=Buffer(device.Get(),ti.ResultDataMaxSizeInBytes,false,D3D12_RESOURCE_STATE_RAYTRACING_ACCELERATION_STRUCTURE);
    D3D12_BUILD_RAYTRACING_ACCELERATION_STRUCTURE_DESC build{};build.Inputs=bottom;build.ScratchAccelerationStructureData=scratch->GetGPUVirtualAddress();build.DestAccelerationStructureData=blas->GetGPUVirtualAddress();
    commands->BuildRaytracingAccelerationStructure(&build,0,nullptr);
    D3D12_RESOURCE_BARRIER barrier{};barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_UAV;commands->ResourceBarrier(1,&barrier);
    D3D12_RAYTRACING_INSTANCE_DESC inst{};inst.Transform[0][0]=inst.Transform[1][1]=inst.Transform[2][2]=1;inst.InstanceMask=255;inst.AccelerationStructure=blas->GetGPUVirtualAddress();
    auto instances=Buffer(device.Get(),sizeof(inst),true,D3D12_RESOURCE_STATE_GENERIC_READ);Upload(instances.Get(),&inst,sizeof(inst));
    top.InstanceDescs=instances->GetGPUVirtualAddress();build.Inputs=top;build.DestAccelerationStructureData=tlas->GetGPUVirtualAddress();
    commands->BuildRaytracingAccelerationStructure(&build,0,nullptr);commands->ResourceBarrier(1,&barrier);
    D3D12_HEAP_PROPERTIES heap{};heap.Type=D3D12_HEAP_TYPE_DEFAULT;heap.CreationNodeMask=heap.VisibleNodeMask=1;
    D3D12_RESOURCE_DESC td{};td.Dimension=D3D12_RESOURCE_DIMENSION_TEXTURE2D;td.Width=td.Height=128;td.DepthOrArraySize=td.MipLevels=td.SampleDesc.Count=1;td.Format=DXGI_FORMAT_R32_FLOAT;
    td.Flags=D3D12_RESOURCE_FLAG_ALLOW_UNORDERED_ACCESS|D3D12_RESOURCE_FLAG_ALLOW_SIMULTANEOUS_ACCESS;
    ComPtr<ID3D12Resource> output;
    HR(device->CreateCommittedResource(&heap,D3D12_HEAP_FLAG_SHARED,&td,D3D12_RESOURCE_STATE_COMMON,nullptr,GET(ID3D12Resource,output)));
    Handle shared;HR(device->CreateSharedHandle(output.Get(),nullptr,GENERIC_ALL,nullptr,&shared.h));
    ComPtr<ID3D11Texture2D> texture11;HR(device11->OpenSharedResource1(shared.h,GET(ID3D11Texture2D,texture11)));
    ComPtr<ID3D11UnorderedAccessView> uav11;HR(device11->CreateUnorderedAccessView(texture11.Get(),nullptr,&uav11));
    ComPtr<ID3D12Fence> fence;HR(device->CreateFence(0,D3D12_FENCE_FLAG_SHARED,GET(ID3D12Fence,fence)));
    Handle fh;HR(device->CreateSharedHandle(fence.Get(),nullptr,GENERIC_ALL,nullptr,&fh.h));
    ComPtr<ID3D11Fence> fence11;HR(device11->OpenSharedFence(fh.h,GET(ID3D11Fence,fence11)));
    const float sentinel[]={.5f,.5f,.5f,.5f};context->ClearUnorderedAccessViewFloat(uav11.Get(),sentinel);
    HR(context->Signal(fence11.Get(),1));context->Flush();HR(queue->Wait(fence.Get(),1));
    D3D12_DESCRIPTOR_HEAP_DESC hd{};hd.Type=D3D12_DESCRIPTOR_HEAP_TYPE_CBV_SRV_UAV;hd.NumDescriptors=1;hd.Flags=D3D12_DESCRIPTOR_HEAP_FLAG_SHADER_VISIBLE;
    ComPtr<ID3D12DescriptorHeap> descriptors;HR(device->CreateDescriptorHeap(&hd,GET(ID3D12DescriptorHeap,descriptors)));
    D3D12_CPU_DESCRIPTOR_HANDLE cpu{};D3D12_GPU_DESCRIPTOR_HANDLE gpu{};
#ifdef _MSC_VER
    cpu=descriptors->GetCPUDescriptorHandleForHeapStart();gpu=descriptors->GetGPUDescriptorHandleForHeapStart();
#else
    descriptors->GetCPUDescriptorHandleForHeapStart(&cpu);descriptors->GetGPUDescriptorHandleForHeapStart(&gpu);
#endif
    D3D12_UNORDERED_ACCESS_VIEW_DESC ud{};ud.Format=td.Format;ud.ViewDimension=D3D12_UAV_DIMENSION_TEXTURE2D;device->CreateUnorderedAccessView(output.Get(),nullptr,&ud,cpu);
    D3D12_DESCRIPTOR_RANGE range{};range.RangeType=D3D12_DESCRIPTOR_RANGE_TYPE_UAV;range.NumDescriptors=1;
    D3D12_ROOT_PARAMETER parameters[2]{};parameters[0].ParameterType=D3D12_ROOT_PARAMETER_TYPE_SRV;
    parameters[1].ParameterType=D3D12_ROOT_PARAMETER_TYPE_DESCRIPTOR_TABLE;parameters[1].DescriptorTable.NumDescriptorRanges=1;parameters[1].DescriptorTable.pDescriptorRanges=&range;
    D3D12_ROOT_SIGNATURE_DESC rd{};rd.NumParameters=2;rd.pParameters=parameters;
    ComPtr<ID3DBlob> serialized,errors;HR(D3D12SerializeRootSignature(&rd,D3D_ROOT_SIGNATURE_VERSION_1,&serialized,&errors));
    ComPtr<ID3D12RootSignature> root;HR(device->CreateRootSignature(0,serialized->GetBufferPointer(),serialized->GetBufferSize(),GET(ID3D12RootSignature,root)));
    wchar_t module[32768]{};DWORD length=GetModuleFileNameW(nullptr,module,32768);if(!length || length==32768) throw std::runtime_error("Executable path");
    std::ifstream file(std::filesystem::path(module).parent_path()/"Probe.cso",std::ios::binary);if(!file) throw std::runtime_error("Missing Probe.cso");
    std::vector<char> code{std::istreambuf_iterator<char>(file),{}};
    D3D12_COMPUTE_PIPELINE_STATE_DESC pd{};pd.pRootSignature=root.Get();pd.CS={code.data(),code.size()};
    ComPtr<ID3D12PipelineState> pipeline;HR(device->CreateComputePipelineState(&pd,GET(ID3D12PipelineState,pipeline)));
    barrier={};barrier.Type=D3D12_RESOURCE_BARRIER_TYPE_TRANSITION;barrier.Transition.pResource=output.Get();barrier.Transition.Subresource=D3D12_RESOURCE_BARRIER_ALL_SUBRESOURCES;
    barrier.Transition.StateBefore=D3D12_RESOURCE_STATE_COMMON;barrier.Transition.StateAfter=D3D12_RESOURCE_STATE_UNORDERED_ACCESS;commands->ResourceBarrier(1,&barrier);
    commands->SetPipelineState(pipeline.Get());commands->SetComputeRootSignature(root.Get());ID3D12DescriptorHeap* heaps[]={descriptors.Get()};commands->SetDescriptorHeaps(1,heaps);
    commands->SetComputeRootShaderResourceView(0,tlas->GetGPUVirtualAddress());commands->SetComputeRootDescriptorTable(1,gpu);commands->Dispatch(16,16,1);
    barrier.Transition.StateBefore=D3D12_RESOURCE_STATE_UNORDERED_ACCESS;barrier.Transition.StateAfter=D3D12_RESOURCE_STATE_COMMON;commands->ResourceBarrier(1,&barrier);HR(commands->Close());
    ID3D12CommandList* lists[]={commands.Get()};queue->ExecuteCommandLists(1,lists);HR(queue->Signal(fence.Get(),2));HR(context->Wait(fence11.Get(),2));
    D3D11_TEXTURE2D_DESC sd{};texture11->GetDesc(&sd);sd.Usage=D3D11_USAGE_STAGING;sd.BindFlags=sd.MiscFlags=0;sd.CPUAccessFlags=D3D11_CPU_ACCESS_READ;
    ComPtr<ID3D11Texture2D> staging;HR(device11->CreateTexture2D(&sd,nullptr,&staging));context->CopyResource(staging.Get(),texture11.Get());
    HR(context->Signal(fence11.Get(),3));context->Flush();Handle done;done.h=CreateEventW(nullptr,FALSE,FALSE,nullptr);if(!done.h) throw std::runtime_error("CreateEvent");
    HR(fence->SetEventOnCompletion(3,done.h));if(WaitForSingleObject(done.h,30000)!=WAIT_OBJECT_0) throw std::runtime_error("GPU timeout");
    D3D11_MAPPED_SUBRESOURCE mapped{};HR(context->Map(staging.Get(),0,D3D11_MAP_READ,0,&mapped));
    unsigned mismatch=0;std::ofstream image("Probe.pgm",std::ios::binary);image<<"P5\n128 128\n255\n";
    for(unsigned y=0;y<128;++y){const auto* row=reinterpret_cast<const float*>(static_cast<const char*>(mapped.pData)+y*mapped.RowPitch);
        for(unsigned x=0;x<128;++x){float expected=(x>=32&&x<96&&y>=32&&y<96)?0.f:1.f;
            if(!std::isfinite(row[x])||std::abs(row[x]-expected)>.001f)++mismatch;
            image.put(row[x]>=.5f?char(255):char(0));}}
    context->Unmap(staging.Get(),0);HR(device->GetDeviceRemovedReason());
    std::cout<<"BLAS bytes requested: "<<bi.ResultDataMaxSizeInBytes<<" TLAS: "<<ti.ResultDataMaxSizeInBytes<<"\n16384 pixel comparisons, mismatches: "<<mismatch<<'\n';
    std::cout<<(mismatch?"FAIL\n":"PASS: hardware rays + DX11 readback\n");return mismatch?2:0;
}
int main(){try{return Run();}catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
